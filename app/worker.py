from queue import Queue, Empty
from threading import Thread, Event
from sqlmodel import Session, select
from .models import Task, TaskStatus
from .db import engine
from .ytdlp_wrapper import download_video
from .ffmpeg_wrapper import process_video
from .auto_pipeline import AutoPipeline
import os
from datetime import datetime, timezone


def time_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
VIDEOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "videos"))
CLIPS_DIR = os.path.abspath(os.path.join(BASE_DIR, "clips"))
RAW_DIR = VIDEOS_DIR
PROCESSED_DIR = VIDEOS_DIR


download_queue: "Queue[int]" = Queue()
process_queue: "Queue[int]" = Queue()

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
    enqueue_pending_from_db()
    t1 = Thread(target=download_worker, name="download_worker", daemon=True)
    t2 = Thread(target=process_worker, name="process_worker", daemon=True)
    t1.start()
    t2.start()


def add_task_to_download(task_id: int):
    download_queue.put(task_id)
