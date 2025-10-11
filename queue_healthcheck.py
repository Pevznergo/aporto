"""
Queue Healthcheck Worker - добавить в app/worker.py

Этот worker проверяет застрявшие задачи и перезапускает их
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from .models import UpscaleTask, UpscaleStatus
from .db import engine

def queue_healthcheck_worker():
    """
    Healthcheck worker для отслеживания зависших задач.
    Запускается каждые 5 минут и проверяет:
    1. Задачи в состоянии 'queued' но не в стадии 'queued' дольше 10 минут
    2. Задачи в стадии 'uploading' дольше 30 минут
    3. Задачи в стадии 'processing' дольше 60 минут
    """
    while not stop_event.is_set():
        try:
            with Session(engine) as session:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                
                # Найти застрявшие задачи
                stuck_tasks = []
                
                # 1. Задачи в состоянии queued но не в стадии queued > 10 минут
                cutoff_10min = now - timedelta(minutes=10)
                queued_stuck = session.exec(
                    select(UpscaleTask).where(
                        UpscaleTask.status == UpscaleStatus.QUEUED,
                        UpscaleTask.stage != "queued",
                        UpscaleTask.updated_at < cutoff_10min
                    )
                ).all()
                stuck_tasks.extend(queued_stuck)
                
                # 2. Задачи в стадии uploading > 30 минут
                cutoff_30min = now - timedelta(minutes=30)
                uploading_stuck = session.exec(
                    select(UpscaleTask).where(
                        UpscaleTask.stage == "uploading",
                        UpscaleTask.updated_at < cutoff_30min
                    )
                ).all()
                stuck_tasks.extend(uploading_stuck)
                
                # 3. Задачи в стадии processing > 60 минут
                cutoff_60min = now - timedelta(minutes=60)
                processing_stuck = session.exec(
                    select(UpscaleTask).where(
                        UpscaleTask.stage == "processing",
                        UpscaleTask.updated_at < cutoff_60min
                    )
                ).all()
                stuck_tasks.extend(processing_stuck)
                
                # Исправить застрявшие задачи
                for task in stuck_tasks:
                    logging.warning(f"[healthcheck] Found stuck task {task.id}: {task.status}/{task.stage}, last update: {task.updated_at}")
                    
                    # Сбросить в очередь заново
                    task.status = UpscaleStatus.QUEUED
                    task.stage = "queued"
                    task.progress = 0
                    task.error = f"Auto-reset by healthcheck (was stuck in {task.stage})"
                    task.updated_at = now
                    session.add(task)
                    
                    # Добавить в очередь загрузки заново
                    try:
                        upload_upscale_queue.put(task.id)
                        logging.info(f"[healthcheck] Re-queued stuck task {task.id}")
                    except Exception as e:
                        logging.error(f"[healthcheck] Failed to re-queue task {task.id}: {e}")
                
                if stuck_tasks:
                    session.commit()
                    logging.info(f"[healthcheck] Fixed {len(stuck_tasks)} stuck tasks")
                    
        except Exception as e:
            logging.error(f"[healthcheck] Error: {e}")
        
        # Ждать 5 минут до следующей проверки
        time.sleep(300)

# Добавить в start_workers():
def start_workers_with_healthcheck():
    # ... existing workers ...
    
    # Добавить healthcheck worker
    healthcheck_thread = Thread(target=queue_healthcheck_worker, name="queue_healthcheck", daemon=True)
    healthcheck_thread.start()
    
    logging.info("Started queue healthcheck worker")