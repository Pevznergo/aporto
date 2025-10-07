from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class TaskStatus:
    QUEUED_DOWNLOAD = "queued_download"
    DOWNLOADING = "downloading"
    QUEUED_PROCESS = "queued_process"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"
    CANCELED = "canceled"


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    mode: str = Field(default="simple")  # "simple" | "auto"
    status: str = Field(default=TaskStatus.QUEUED_DOWNLOAD)
    # Текущая стадия процесса (для UI): downloading | transcribing | gpt | cutting | done | error
    stage: Optional[str] = None
    # Прогресс в процентах (0..100)
    progress: Optional[int] = None

    video_id: Optional[str] = None
    original_filename: Optional[str] = None
    downloaded_path: Optional[str] = None
    processed_path: Optional[str] = None  # для simple
    # auto-поле: куда сложены клипы
    clips_dir: Optional[str] = None
    transcript_path: Optional[str] = None
    clips_json_path: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UpscaleStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class UpscaleTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str  # local path under to_upscale/
    status: str = Field(default=UpscaleStatus.QUEUED)
    stage: Optional[str] = None  # ensuring_instance|uploading|processing|downloading|done|error
    progress: Optional[int] = 0
    
    vast_instance_id: Optional[str] = None
    vast_job_id: Optional[str] = None
    
    result_path: Optional[str] = None  # local path under clips_upscaled/
    error: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DownloadedVideo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
