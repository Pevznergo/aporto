from queue import Queue, Empty
from threading import Thread, Event
from sqlmodel import Session, select
from fastapi import HTTPException
from .models import Task, TaskStatus, UpscaleTask, UpscaleStatus
from .db import engine
from .ytdlp_wrapper import download_video
from .ffmpeg_wrapper import process_video
from .auto_pipeline import AutoPipeline
import os
import time
from datetime import datetime, timezone
import os
from datetime import datetime, timezone


def time_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
VIDEOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "videos"))
CLIPS_DIR = os.path.abspath(os.path.join(BASE_DIR, "clips"))
CLIPS_UPSCALED_DIR = os.path.abspath(os.path.join(BASE_DIR, "clips_upscaled"))
TO_UPSCALE_DIR = os.path.abspath(os.path.join(BASE_DIR, "to_upscale"))
RAW_DIR = VIDEOS_DIR
PROCESSED_DIR = VIDEOS_DIR

# Allowed media extensions for upscale scanning
UPSCALE_MEDIA_EXTS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v",
    ".mpeg", ".mpg", ".m2ts", ".ts", ".flv"
}

def _is_media_file(name: str) -> bool:
    if not name or name.startswith('.'):
        return False
    ext = os.path.splitext(name)[1].lower()
    return ext in UPSCALE_MEDIA_EXTS


download_queue: "Queue[int]" = Queue()
process_queue: "Queue[int]" = Queue()

# Upscale queues and control
upscale_queue: "Queue[int]" = Queue()
# Default is 2, but will be read dynamically from config
UPSCALE_CONCURRENCY_DEFAULT = 2
_active_upscale = 0

stop_event = Event()


def enqueue_pending_from_db():
    with Session(engine) as session:
        status_and_queue = (
            (TaskStatus.QUEUED_DOWNLOAD, download_queue),
            (TaskStatus.DOWNLOADING, download_queue),
            (TaskStatus.QUEUED_PROCESS, process_queue),
            (TaskStatus.PROCESSING, process_queue),
        )
        for status, q in status_and_queue:
            tasks = session.exec(select(Task).where(Task.status == status)).all()
            for t in tasks:
                # если были прерваны, вернём в очередь
                if status == TaskStatus.DOWNLOADING:
                    t.status = TaskStatus.QUEUED_DOWNLOAD
                    t.updated_at = time_utc()
                    session.add(t)
                elif status == TaskStatus.PROCESSING:
                    t.status = TaskStatus.QUEUED_PROCESS
                    t.updated_at = time_utc()
                    session.add(t)
                q.put(t.id)
        session.commit()


def download_worker():
    while not stop_event.is_set():
        try:
            task_id = download_queue.get(timeout=0.5)
        except Empty:
            continue
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                download_queue.task_done()
                continue
            try:
                task.status = TaskStatus.DOWNLOADING
                task.stage = "downloading"
                task.progress = 5
                task.updated_at = time_utc()
                session.add(task)
                session.commit()

                video_id, title, file_path = download_video(task.url, RAW_DIR)
                task.video_id = video_id
                task.original_filename = title
                task.downloaded_path = file_path
                task.status = TaskStatus.QUEUED_PROCESS
                task.stage = "queued_process"
                task.progress = 25
                task.updated_at = time_utc()
                session.add(task)
                session.commit()

                process_queue.put(task.id)
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.ERROR
                task.stage = "error"
                task.progress = None
                task.updated_at = time_utc()
                session.add(task)
                session.commit()
            finally:
                download_queue.task_done()


def process_worker():
    # Lazy init of heavy pipeline to avoid loading Whisper before needed
    auto_pipeline = None
    while not stop_event.is_set():
        try:
            task_id = process_queue.get(timeout=0.5)
        except Empty:
            continue
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                process_queue.task_done()
                continue
            try:
                task.status = TaskStatus.PROCESSING
                task.updated_at = time_utc()
                session.add(task)
                session.commit()

                if getattr(task, "mode", "simple") == "auto":
                    if auto_pipeline is None:
                        # Model size configurable via env WHISPER_MODEL
                        model_size = os.getenv("WHISPER_MODEL", "small")
                        auto_pipeline = AutoPipeline(model_size=model_size)
                    # Prepare output dir under clips/<basename>
                    base_name = os.path.splitext(os.path.basename(task.downloaded_path or "video"))[0]
                    out_dir = os.path.join(CLIPS_DIR, base_name)
                    os.makedirs(out_dir, exist_ok=True)

                    # 1) Transcribe
                    task.stage = "transcribing"
                    task.progress = 40
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()
                    transcript_path = os.path.join(out_dir, f"{base_name}_transcript.json")
                    transcript = auto_pipeline.transcribe_video(task.downloaded_path, transcript_path)

                    # 2) Ask GPT
                    task.stage = "gpt"
                    task.progress = 70
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()
                    clips_json_path = os.path.join(out_dir, f"{base_name}_clips.json")
                    clips = auto_pipeline.ask_gpt(transcript, clips_json_path)

                    # 3) Cut clips
                    total = max(len(clips), 1)
                    task.stage = "cutting"
                    task.progress = 80
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()

                    def on_progress(i: int, total_clips: int):
                        # Прогресс от 80 до 100 в зависимости от продвинутых клипов
                        pct = 80 + int((i / max(total_clips, 1)) * 20)
                        with Session(engine) as ses2:
                            t2 = ses2.get(Task, task.id)
                            if t2:
                                t2.progress = min(pct, 99)
                                t2.updated_at = time_utc()
                                ses2.add(t2)
                                ses2.commit()

                    clip_files = auto_pipeline.cut_clips(task.downloaded_path, clips, out_dir, on_progress=on_progress)

                    # Успешно: сохраняем пути, отмечаем done, и только теперь можно удалить исходник, если нужно
                    task.clips_dir = out_dir
                    task.transcript_path = transcript_path
                    task.clips_json_path = clips_json_path
                    task.processed_path = None
                    task.status = TaskStatus.DONE
                    task.stage = "done"
                    task.progress = 100
                else:
                    task.stage = "cutting"
                    task.progress = 80
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()
                    output_path = process_video(task.downloaded_path, PROCESSED_DIR, task.start_time, task.end_time)
                    task.processed_path = output_path
                    task.status = TaskStatus.DONE
                    task.stage = "done"
                    task.progress = 100

                task.updated_at = time_utc()
                session.add(task)
                session.commit()
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.ERROR
                task.stage = "error"
                task.progress = None
                task.updated_at = time_utc()
                session.add(task)
                session.commit()
            finally:
                process_queue.task_done()


def start_workers():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(CLIPS_UPSCALED_DIR, exist_ok=True)
    os.makedirs(TO_UPSCALE_DIR, exist_ok=True)
    enqueue_pending_from_db()
    t1 = Thread(target=download_worker, name="download_worker", daemon=True)
    t2 = Thread(target=process_worker, name="process_worker", daemon=True)
    t3 = Thread(target=upscale_watcher, name="upscale_watcher", daemon=True)
    t4 = Thread(target=upscale_worker, name="upscale_worker", daemon=True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()


def add_task_to_download(task_id: int):
    download_queue.put(task_id)


# ========== Upscale support ==========
from .upscale_vast import VastManager

_vast = None


def get_vast():
    global _vast
    if _vast is None:
        _vast = VastManager()
    return _vast


def upscale_watcher():
    """
    Scan TO_UPSCALE_DIR periodically and enqueue new files as UpscaleTask.
    Only media files are considered; hidden/system files are ignored.
    """
    last_seen = set()
    while not stop_event.is_set():
        try:
            current = set()
            for name in os.listdir(TO_UPSCALE_DIR):
                if not _is_media_file(name):
                    continue
                path = os.path.join(TO_UPSCALE_DIR, name)
                if os.path.isfile(path):
                    current.add(path)
                    if path not in last_seen:
                        # Create task if not exists
                        with Session(engine) as session:
                            existing = session.exec(select(UpscaleTask).where(UpscaleTask.file_path == path)).first()
                            if not existing:
                                ut = UpscaleTask(file_path=path, status=UpscaleStatus.QUEUED, stage="queued", progress=0)
                                session.add(ut)
                                session.commit()
                                session.refresh(ut)
                                upscale_queue.put(ut.id)
            last_seen = current
            time.sleep(2.0)
        except Exception:
            time.sleep(2.0)


def upscale_worker():
    global _active_upscale
    from .upscale_config import get_upscale_concurrency
    vast = get_vast()
    while not stop_event.is_set():
        try:
            task_id = upscale_queue.get(timeout=0.5)
        except Empty:
            # No pending, if none active — try to stop instance
            if _active_upscale == 0:
                try:
                    vast.stop_instance_if_idle()
                except Exception:
                    pass
            continue
        with Session(engine) as session:
            ut = session.get(UpscaleTask, task_id)
            if not ut:
                upscale_queue.task_done()
                continue
            try:
                # Enforce concurrency (read dynamic value)
                while _active_upscale >= get_upscale_concurrency() and not stop_event.is_set():
                    time.sleep(0.5)
                _active_upscale += 1

                # Ensure instance
                ut.stage = "ensuring_instance"
                ut.status = UpscaleStatus.PROCESSING
                ut.progress = 5
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

                inst = vast.ensure_instance_running()
                ut.vast_instance_id = str(inst.get("id"))
                session.add(ut)
                session.commit()

                # Upload
                ut.stage = "uploading"
                ut.progress = 20
                session.add(ut)
                session.commit()
                remote_in, remote_out = vast.upload_and_plan_paths(inst, ut.file_path)

                # Submit
                ut.stage = "processing"
                ut.progress = 40
                session.add(ut)
                session.commit()
                job_id = vast.submit_job(inst, remote_in, remote_out)
                ut.vast_job_id = str(job_id)
                session.add(ut)
                session.commit()

                # Poll
                while True:
                    status = vast.job_status(inst, job_id)
                    if status == "processing":
                        # Bump progress gradually 40..85
                        ut.progress = min((ut.progress or 40) + 2, 85)
                        ut.updated_at = time_utc()
                        session.add(ut)
                        session.commit()
                        time.sleep(3)
                    elif status == "completed":
                        break
                    else:
                        raise RuntimeError(f"Upscale job failed: status={status}")

                # Download
                ut.stage = "downloading"
                ut.progress = 90
                session.add(ut)
                session.commit()
                local_out = vast.download_result(inst, remote_out, CLIPS_UPSCALED_DIR)
                ut.result_path = local_out
                ut.stage = "done"
                ut.status = UpscaleStatus.DONE
                ut.progress = 100
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

            except Exception as e:
                ut.status = UpscaleStatus.ERROR
                ut.stage = "error"
                ut.error = str(e)
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()
            finally:
                _active_upscale = max(0, _active_upscale - 1)
                upscale_queue.task_done()


def trigger_upscale_scan():
    # force scan by placing all files into queue if not yet queued
    with Session(engine) as session:
        for name in os.listdir(TO_UPSCALE_DIR):
            if not _is_media_file(name):
                continue
            path = os.path.join(TO_UPSCALE_DIR, name)
            if not os.path.isfile(path):
                continue
            existing = session.exec(select(UpscaleTask).where(UpscaleTask.file_path == path)).first()
            if not existing:
                ut = UpscaleTask(file_path=path, status=UpscaleStatus.QUEUED, stage="queued", progress=0)
                session.add(ut)
                session.commit()
                session.refresh(ut)
                upscale_queue.put(ut.id)


def list_upscale_tasks():
    with Session(engine) as session:
        items = session.exec(select(UpscaleTask).order_by(UpscaleTask.id.desc())).all()
        return items


def retry_upscale_task(task_id: int):
    with Session(engine) as session:
        ut = session.get(UpscaleTask, task_id)
        if not ut:
            raise HTTPException(status_code=404, detail="Upscale task not found")
        ut.status = UpscaleStatus.QUEUED
        ut.stage = "queued"
        ut.progress = 0
        ut.error = None
        session.add(ut)
        session.commit()
        upscale_queue.put(ut.id)
        return ut


def _purge_from_queue(q: Queue, task_id: int):
    """Remove all occurrences of task_id from queue q (best-effort)."""
    tmp = []
    while True:
        try:
            item = q.get_nowait()
            if item != task_id:
                tmp.append(item)
        except Empty:
            break
    for item in tmp:
        q.put(item)


def delete_upscale_task(task_id: int):
    with Session(engine) as session:
        ut = session.get(UpscaleTask, task_id)
        if not ut:
            raise HTTPException(status_code=404, detail="Upscale task not found")
        # Best-effort: allow deletion even if processing; worker may still be running
        # but will not be able to update a deleted row.
        # Remove from queue if present
        _purge_from_queue(upscale_queue, task_id)
        # Delete input file (safety: only under TO_UPSCALE_DIR)
        try:
            if ut.file_path and os.path.isfile(ut.file_path):
                safe_prefix = TO_UPSCALE_DIR + os.sep
                if ut.file_path.startswith(safe_prefix) or ut.file_path == TO_UPSCALE_DIR:
                    os.remove(ut.file_path)
        except Exception:
            pass
        # Delete DB row
        session.delete(ut)
        session.commit()
        return {"ok": True}
