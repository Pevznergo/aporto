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
import threading
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
# Upload queue (sequential uploads by default)
upload_upscale_queue: "Queue[int]" = Queue()
# After upload, tasks go to process queue (GPU-bound)
process_upscale_queue: "Queue[int]" = Queue()
# Result download queue (sequential by default)
result_download_queue: "Queue[int]" = Queue()
# Default is 2, but will be read dynamically from config
UPSCALE_CONCURRENCY_DEFAULT = 2
_active_upscale = 0

# Keep remote paths for tasks (remote_in, remote_out)
_remote_paths: dict[int, tuple[str, str]] = {}
_remote_lock = threading.Lock()

# Separate concurrency for uploads (SSH/SCP) so uploads do not block GPU slots
def get_upload_concurrency() -> int:
    try:
        val = int(os.getenv("UPSCALE_UPLOAD_CONCURRENCY", "1"))
        return max(1, val)
    except Exception:
        return 1

_upload_sem = threading.Semaphore(get_upload_concurrency())

# Separate concurrency for downloading results (sequential by default)

def get_result_download_concurrency() -> int:
    try:
        val = int(os.getenv("UPSCALE_RESULT_DOWNLOAD_CONCURRENCY", "1"))
        return max(1, val)
    except Exception:
        return 1

_result_dl_sem = threading.Semaphore(get_result_download_concurrency())

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
                # If GPU cut is enabled and mode is auto, run remote pipeline instead of local download
                gpu_cut = str(os.getenv("CUT_ON_GPU", "")).lower() in ("1", "true", "yes")
                if gpu_cut and getattr(task, "mode", "simple") == "auto":
                    from .upscale_vast import VastManager
                    vm = VastManager()
                    task.stage = "ensuring_instance"
                    task.progress = 5
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()

                    inst = vm.ensure_instance_running()
                    # Submit remote cut job
                    task.stage = "remote_submit"
                    task.progress = 10
                    session.add(task)
                    session.commit()
                    model_size = os.getenv("WHISPER_MODEL", "small")
                    job_id = vm.submit_cut_url(inst, task.url, model_size=model_size)
                    task.stage = "remote_processing"
                    task.status = TaskStatus.PROCESSING
                    task.progress = 30
                    task.updated_at = time_utc()
                    session.add(task)
                    session.commit()

                    # Poll
                    last_pct = 30
                    while True:
                        info = vm.cut_status(inst, job_id)
                        st = info.get("status")
                        if st == "processing":
                            last_pct = min(last_pct + 3, 85)
                            task.progress = last_pct
                            task.updated_at = time_utc()
                            session.add(task)
                            session.commit()
                            time.sleep(5)
                        elif st == "completed":
                            remote_zip = info.get("output_archive")
                            if not remote_zip:
                                raise RuntimeError("Remote cut completed but no archive path provided")
                            # Download archive to local cuted dir
                            local_cuted_base = os.path.abspath(os.path.join(BASE_DIR, "cuted"))
                            os.makedirs(local_cuted_base, exist_ok=True)
                            task.stage = "downloading_results"
                            task.progress = 90
                            session.add(task)
                            session.commit()
                            local_zip = vm.download_result(inst, remote_zip, local_cuted_base)
                            # Unzip into folder
                            import zipfile
                            base_name = os.path.splitext(os.path.basename(local_zip))[0]
                            dest_dir = os.path.join(local_cuted_base, base_name)
                            os.makedirs(dest_dir, exist_ok=True)
                            with zipfile.ZipFile(local_zip, 'r') as zf:
                                zf.extractall(os.path.join(local_cuted_base))
                            # Update task
                            task.clips_dir = dest_dir
                            # Try to set transcript and clips json paths if present
                            tr_path = os.path.join(dest_dir, f"{base_name}_transcript.json")
                            cj_path = os.path.join(dest_dir, f"{base_name}_clips.json")
                            task.transcript_path = tr_path if os.path.exists(tr_path) else None
                            task.clips_json_path = cj_path if os.path.exists(cj_path) else None
                            task.status = TaskStatus.DONE
                            task.stage = "done"
                            task.progress = 100
                            task.updated_at = time_utc()
                            session.add(task)
                            session.commit()
                            break
                        else:
                            raise RuntimeError(f"Remote cut job failed: status={st}")
                else:
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
                    # Save to downloads registry (dedupe by URL)
                    try:
                        from .models import DownloadedVideo
                        exists = session.exec(select(DownloadedVideo).where(DownloadedVideo.url == task.url)).first()
                        if not exists:
                            session.add(DownloadedVideo(url=task.url, title=title))
                            session.commit()
                    except Exception:
                        pass
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
    t4 = Thread(target=upload_upscale_worker, name="upload_upscale_worker", daemon=True)
    # Start as many GPU workers as concurrency allows
    from .upscale_config import get_upscale_concurrency
    gpu_workers = []
    for i in range(max(1, get_upscale_concurrency())):
        gpu_workers.append(Thread(target=process_upscale_worker, name=f"process_upscale_worker_{i+1}", daemon=True))
    t6 = Thread(target=result_download_worker, name="result_download_worker", daemon=True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    for tw in gpu_workers:
        tw.start()
    t6.start()
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


def _stop_instance_if_fully_idle():
    """Best-effort: stop instance when there is no work anywhere.
    Calls VastManager.stop_instance_if_idle(), which enforces cooldown and activity windows.
    """
    vast = get_vast()
    try:
        if _active_upscale == 0 \
           and upload_upscale_queue.empty() \
           and process_upscale_queue.empty() \
           and result_download_queue.empty():
            vast.stop_instance_if_idle()
    except Exception:
        pass


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
                                upload_upscale_queue.put(ut.id)
            last_seen = current
            # If there are no files to upscale and queues are empty, consider stopping instance
            if not current and upload_upscale_queue.empty() and process_upscale_queue.empty() and result_download_queue.empty() and _active_upscale == 0:
                _stop_instance_if_fully_idle()
            time.sleep(2.0)
        except Exception:
            time.sleep(2.0)


def upload_upscale_worker():
    vast = get_vast()
    while not stop_event.is_set():
        try:
            task_id = upload_upscale_queue.get(timeout=0.5)
        except Empty:
            # Attempt to stop instance if fully idle
            _stop_instance_if_fully_idle()
            continue
        with Session(engine) as session:
            ut = session.get(UpscaleTask, task_id)
            if not ut:
                upload_upscale_queue.task_done()
                continue
            try:
                # Ensure instance
                ut.stage = "ensuring_instance"
                # Keep status in QUEUED until actual GPU processing begins
                ut.progress = 5
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

                inst = vast.ensure_instance_running()
                ut.vast_instance_id = str(inst.get("id"))
                session.add(ut)
                session.commit()

                # Sequential upload (guarded by semaphore, default 1)
                ut.stage = "uploading"
                ut.progress = 20
                session.add(ut)
                session.commit()
                _upload_sem.acquire()
                try:
                    remote_in, remote_out = vast.upload_and_plan_paths(inst, ut.file_path)
                finally:
                    _upload_sem.release()

                # Store remote paths and enqueue for GPU processing
                with _remote_lock:
                    _remote_paths[task_id] = (remote_in, remote_out)
                ut.stage = "queued_gpu"
                ut.progress = 35
                ut.updated_at = time_utc()
                # Keep status queued while waiting for GPU slot
                ut.status = UpscaleStatus.QUEUED
                session.add(ut)
                session.commit()
                process_upscale_queue.put(task_id)
            except Exception as e:
                ut.status = UpscaleStatus.ERROR
                ut.stage = "error"
                ut.error = str(e)
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()
            finally:
                upload_upscale_queue.task_done()


def process_upscale_worker():
    global _active_upscale
    from .upscale_config import get_upscale_concurrency
    vast = get_vast()
    while not stop_event.is_set():
        try:
            task_id = process_upscale_queue.get(timeout=0.5)
        except Empty:
            # If all idle, consider stopping instance
            if _active_upscale == 0 and upload_upscale_queue.empty() and process_upscale_queue.empty():
                try:
                    vast.stop_instance_if_idle()
                except Exception:
                    pass
            continue
        with Session(engine) as session:
            ut = session.get(UpscaleTask, task_id)
            if not ut:
                process_upscale_queue.task_done()
                continue
            acquired_slot = False
            freed_slot = False
            try:
                # Wait for GPU slot
                while _active_upscale >= get_upscale_concurrency() and not stop_event.is_set():
                    time.sleep(0.5)
                _active_upscale += 1
                acquired_slot = True

                # Submit
                with _remote_lock:
                    remote = _remote_paths.get(task_id)
                if not remote:
                    raise RuntimeError("Remote paths not found for task")
                remote_in, remote_out = remote

                inst = vast.ensure_instance_running()
                ut.stage = "processing"
                ut.status = UpscaleStatus.PROCESSING
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
                        ut.progress = min((ut.progress or 40) + 2, 85)
                        ut.updated_at = time_utc()
                        session.add(ut)
                        session.commit()
                        time.sleep(3)
                    elif status == "completed":
                        break
                    else:
                        raise RuntimeError(f"Upscale job failed: status={status}")

                # Mark ready for download and immediately free GPU slot before enqueueing download
                ut.stage = "queued_result_download"
                ut.progress = 90
                session.add(ut)
                session.commit()
                # Free GPU slot now to allow next GPU job to start while downloading happens
                _active_upscale = max(0, _active_upscale - 1)
                freed_slot = True
                # Enqueue result download and finish this task in the GPU queue
                result_download_queue.put(task_id)
                # Cleanup remote path mapping will be done by result_download_worker after successful download

            except Exception as e:
                ut.status = UpscaleStatus.ERROR
                ut.stage = "error"
                ut.error = str(e)
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()
                # Free GPU slot on error
                if acquired_slot and not freed_slot:
                    _active_upscale = max(0, _active_upscale - 1)
                # Best-effort cleanup mapping on error (no download will occur)
                with _remote_lock:
                    _remote_paths.pop(task_id, None)
            finally:
                process_upscale_queue.task_done()


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
                upload_upscale_queue.put(ut.id)


def list_upscale_tasks():
    with Session(engine) as session:
        items = session.exec(select(UpscaleTask).order_by(UpscaleTask.id.desc())).all()
        return items


def result_download_worker():
    vast = get_vast()
    while not stop_event.is_set():
        try:
            task_id = result_download_queue.get(timeout=0.5)
        except Empty:
            _stop_instance_if_fully_idle()
            time.sleep(0.1)
            continue
        with Session(engine) as session:
            ut = session.get(UpscaleTask, task_id)
            if not ut:
                result_download_queue.task_done()
                continue
            try:
                # Mark downloading stage
                ut.stage = "downloading"
                ut.progress = 90
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

                # Retrieve remote path
                with _remote_lock:
                    remote = _remote_paths.get(task_id)
                if not remote:
                    raise RuntimeError("Remote paths not found for task (download)")
                _, remote_out = remote

                # Ensure instance for SSH context
                inst = vast.ensure_instance_running()

                # Sequential (or limited) result download
                _result_dl_sem.acquire()
                try:
                    local_out = vast.download_result(inst, remote_out, CLIPS_UPSCALED_DIR)
                finally:
                    _result_dl_sem.release()

                ut.result_path = local_out
                ut.stage = "done"
                ut.status = UpscaleStatus.DONE
                ut.progress = 100
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

                # Cleanup mapping for this task
                with _remote_lock:
                    _remote_paths.pop(task_id, None)
            except Exception as e:
                ut.status = UpscaleStatus.ERROR
                ut.stage = "error"
                ut.error = str(e)
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()
            finally:
                result_download_queue.task_done()
                # If this was the last pending work, consider stopping instance
                _stop_instance_if_fully_idle()


def retry_upscale_task(task_id: int):
    with Session(engine) as session:
        ut = session.get(UpscaleTask, task_id)
        if not ut:
            raise HTTPException(status_code=404, detail="Upscale task not found")
        # Reset status and clear transient errors/stages
        ut.status = UpscaleStatus.QUEUED
        ut.stage = "queued"
        ut.progress = 0
        ut.error = None
        session.add(ut)
        session.commit()
        # Start from the beginning of the pipeline: enqueue upload step
        upload_upscale_queue.put(ut.id)
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
        # Remove from queues if present
        _purge_from_queue(upload_upscale_queue, task_id)
        _purge_from_queue(process_upscale_queue, task_id)
        # Clean mapping
        with _remote_lock:
            _remote_paths.pop(task_id, None)
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
