from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
import logging

# Use PostgreSQL URL from environment or fallback to SQLite for development
POSTGRES_URL = os.getenv("POSTGRES_URL")
if POSTGRES_URL:
    engine = create_engine(POSTGRES_URL, echo=False)
else:
    # Fallback to SQLite for development
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def _mask_dsn(dsn: str) -> str:
    try:
        # Mask credentials in DSN: postgresql://user:pass@host:port/db?...
        if "://" in dsn and "@" in dsn:
            scheme, rest = dsn.split("://", 1)
            creds_host = rest.split("@", 1)
            if len(creds_host) == 2:
                host_part = creds_host[1]
                return f"{scheme}://***:***@{host_part}"
    except Exception:
        pass
    return dsn


def init_db():
    try:
        masked = _mask_dsn(POSTGRES_URL) if POSTGRES_URL else f"sqlite:///{DB_PATH}"
        logging.info(f"[db] Initializing DB engine: {masked}")
        # Fast connectivity check
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logging.info("[db] Connectivity OK")
    except Exception as e:
        logging.error(f"[db] Connectivity check failed: {type(e).__name__}: {e}")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
