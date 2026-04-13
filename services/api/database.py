from __future__ import annotations

import os

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _is_serverless_runtime() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def _default_db_url() -> str:
    # Lambda-based runtimes only allow writing under /tmp.
    if _is_serverless_runtime():
        return "sqlite:////tmp/litter_events.db"
    return "sqlite:///./litter_events.db"


DB_URL = os.getenv("LITTER_DB_URL", _default_db_url())

if DB_URL.startswith("sqlite"):
    sqlite_kwargs = {
        "connect_args": {"check_same_thread": False, "timeout": 30},
        "pool_pre_ping": True,
    }
    if not _is_serverless_runtime():
        sqlite_kwargs.update(
            {
                "pool_size": 40,
                "max_overflow": 80,
                "pool_timeout": 30,
            }
        )

    engine = create_engine(DB_URL, **sqlite_kwargs)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL can fail in restricted filesystems; ignore and continue.
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()
else:
    engine = create_engine(
        DB_URL,
        pool_size=40,
        max_overflow=80,
        pool_timeout=30,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
