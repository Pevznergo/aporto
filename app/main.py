from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
import os
import requests

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from .db import init_db, get_session
from .models import Task, TaskStatus, UpscaleTask, UpscaleStatus, DownloadedVideo
from .schemas import CreateTask, TaskOut, UpscaleTaskOut
from .worker import start_workers, add_task_to_download, VIDEOS_DIR, CLIPS_UPSCALED_DIR, TO_UPSCALE_DIR, trigger_upscale_scan, list_upscale_tasks, retry_upscale_task, delete_upscale_task, clear_all_upscale_tasks, delete_task as delete_cut_task, clear_all_tasks as clear_all_cut_tasks

app = FastAPI(title="Video Cutter Task Manager")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Ensure directories for static mounts exist at import time
for _dir in ("videos", "clips", "clips_upscaled", "cuted"):
    os.makedirs(os.path.join(BASE_DIR, _dir), exist_ok=True)

# CORS for Next.js frontend
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/videos", StaticFiles(directory=os.path.join(BASE_DIR, "videos")), name="videos")
app.mount("/clips", StaticFiles(directory=os.path.join(BASE_DIR, "clips")), name="clips")
app.mount("/clips_upscaled", StaticFiles(directory=os.path.join(BASE_DIR, "clips_upscaled")), name="clips_upscaled")
app.mount("/cuted", StaticFiles(directory=os.path.join(BASE_DIR, "cuted")), name="cuted")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.on_event("startup")
def startup_event():
    init_db()
    start_workers()


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    tasks = session.exec(select(Task).order_by(Task.id.desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks, "videos_dir": VIDEOS_DIR})


@app.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task).order_by(Task.id.desc())).all()
    return tasks


@app.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks", response_model=TaskOut)
def create_task(payload: CreateTask, session: Session = Depends(get_session)):
    # Reject if URL already downloaded and present in the saved list
    existing = session.exec(select(DownloadedVideo).where(DownloadedVideo.url == payload.url)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Это видео уже было скачано ранее")
    task = Task(
        url=payload.url,
        mode=(payload.mode or "simple"),
        start_time=payload.start,
        end_time=payload.end,
        status=TaskStatus.QUEUED_DOWNLOAD,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    add_task_to_download(task.id)
    return task


@app.post("/api/tasks/{task_id}/retry", response_model=TaskOut)
def retry_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.QUEUED_DOWNLOAD
    task.error = None
    session.add(task)
    session.commit()
    add_task_to_download(task.id)
    return task


@app.delete("/api/tasks/{task_id}")
def api_delete_task(task_id: int):
    return delete_cut_task(task_id)


@app.delete("/api/tasks")
def api_clear_tasks():
    return clear_all_cut_tasks()


# Downloads registry API
@app.get("/api/downloads")
def api_list_downloads(session: Session = Depends(get_session)):
    items = session.exec(select(DownloadedVideo).order_by(DownloadedVideo.id.desc())).all()
    return [{"id": d.id, "url": d.url, "title": d.title, "created_at": d.created_at.isoformat()} for d in items]

@app.delete("/api/downloads/{item_id}")
def api_delete_download(item_id: int, session: Session = Depends(get_session)):
    d = session.get(DownloadedVideo, item_id)
    if not d:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    session.delete(d)
    session.commit()
    return {"ok": True}

# Upscale API
@app.get("/api/upscale/tasks", response_model=list[UpscaleTaskOut])
def api_list_upscale_tasks():
    return list_upscale_tasks()


@app.post("/api/upscale/scan")
def api_scan_upscale():
    trigger_upscale_scan()
    return {"ok": True}


@app.post("/api/upscale/tasks/{task_id}/retry", response_model=UpscaleTaskOut)
def api_retry_upscale(task_id: int):
    return retry_upscale_task(task_id)


@app.delete("/api/upscale/tasks/{task_id}")
def api_delete_upscale(task_id: int):
    return delete_upscale_task(task_id)


@app.delete("/api/upscale/tasks")
def api_clear_upscale():
    return clear_all_upscale_tasks()


# Upscale settings and status
from .upscale_config import get_upscale_settings, save_upscale_settings
from .upscale_vast import VastManager

@app.get("/api/upscale/settings")
def api_get_upscale_settings():
    return get_upscale_settings()


@app.put("/api/upscale/settings")
def api_put_upscale_settings(payload: dict):
    return save_upscale_settings(payload)


@app.get("/api/upscale/status")
def api_get_upscale_status():
    # If we are using a direct GPU HTTP endpoint, report its health as the status
    override = os.getenv("VAST_UPSCALE_URL") or ""
    if override.strip():
        try:
            base = override.rstrip('/')
            r = requests.get(f"{base}/health", timeout=3)
            if r.status_code == 200:
                data = r.json()
                # Map GPU API health to a simplified state for the UI
                return {"state": "running" if (data.get("status") == "healthy") else "stopped"}
            return {"state": "unknown"}
        except Exception:
            # GPU API not reachable
            return {"state": "stopped"}
    # Fallback to VastManager status (legacy flow)
    try:
        vm = VastManager()
        state = vm.get_status()
    except Exception:
        state = "unknown"
    return {"state": state}


@app.post("/api/upscale/ensure")
def api_upscale_ensure():
    try:
        vm = VastManager()
        details = vm.ensure_instance_running()
        return {"id": details.get("id"), "state": details.get("actual_status")}
    except Exception as e:
        # Return a clear error instead of hanging/empty reply
        raise HTTPException(status_code=502, detail=f"Failed to ensure instance running: {e}")
