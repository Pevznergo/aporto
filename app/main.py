from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
import os

from .db import init_db, get_session
from .models import Task, TaskStatus
from .schemas import CreateTask, TaskOut
from .worker import start_workers, add_task_to_download, VIDEOS_DIR

app = FastAPI(title="Video Cutter Task Manager")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

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
