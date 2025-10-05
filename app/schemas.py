from pydantic import BaseModel, field_validator
from typing import Optional, Union


class CreateTask(BaseModel):
    url: str
    mode: Optional[str] = "simple"  # "simple" | "auto"
    start: Optional[Union[str, float]] = None
    end: Optional[Union[str, float]] = None

    @staticmethod
    def _parse_ts(val):
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if s == "":
            return None
        try:
            return float(s)
        except Exception:
            pass
        parts = s.split(":")
        parts = [float(p) for p in parts]
        seconds = 0.0
        for p in parts:
            seconds = seconds * 60 + p
        return seconds

    @field_validator("start", "end", mode="before")
    def parse_time(cls, v):
        return cls._parse_ts(v)


class TaskOut(BaseModel):
    id: int
    url: str
    mode: str
    status: str
    stage: Optional[str]
    progress: Optional[int]
    video_id: Optional[str]
    original_filename: Optional[str]
    downloaded_path: Optional[str]
    processed_path: Optional[str]
    clips_dir: Optional[str]
    transcript_path: Optional[str]
    clips_json_path: Optional[str]
    error: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]

    class Config:
        from_attributes = True
