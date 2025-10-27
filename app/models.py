from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


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


class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    short_id: int  # The clip number from GPT response
    title: str
    description: str
    duration_estimate: Optional[str] = None
    hook_strength: Optional[str] = None  # high/medium/low
    why_it_works: Optional[str] = None
    file_path: Optional[str] = None  # Path to the generated clip file
    status: Optional[str] = None  # Published, Cancelled, etc.
    channel: Optional[str] = None  # Channel number: 1, 2, 3, 4
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to fragments
    fragments: List["ClipFragment"] = Relationship(back_populates="clip")


class ClipFragment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clip_id: int = Field(foreign_key="clip.id")
    start_time: str  # Timestamp like "00:05:23.100"
    end_time: str    # Timestamp like "00:05:28.400"
    text: str        # Exact text from transcript
    visual_suggestion: Optional[str] = None
    order: int = Field(default=0)  # Order of fragment within clip
    
    # Relationship back to clip
    clip: Optional[Clip] = Relationship(back_populates="fragments")
