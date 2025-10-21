from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

# Use PostgreSQL URL from environment or fallback to SQLite for development
POSTGRES_URL = os.getenv("POSTGRES_URL")
if POSTGRES_URL:
    engine = create_engine(POSTGRES_URL, echo=False)
else:
    # Fallback to SQLite for development
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
