from __future__ import annotations

import os
import logging

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)


def _is_serverless_runtime() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def _default_db_url() -> str:
    # Lambda-based runtimes only allow writing under /tmp.
    if _is_serverless_runtime():
        logger.warning("Using ephemeral SQLite database in /tmp on serverless runtime. Data WILL be lost. Set LITTER_DB_URL to a persistent database (e.g. PostgreSQL).")
        return "sqlite:////tmp/litter_events.db"
    return "sqlite:///./litter_events.db"


DB_URL = os.getenv("LITTER_DB_URL", _default_db_url())

if DB_URL.startswith("sqlite"):
    # -----------------------------------------------------------------------
    # SQLite: tune for latency, limit pool on serverless
    # -----------------------------------------------------------------------
    if _is_serverless_runtime():
        sqlite_kwargs = {
            "connect_args": {"check_same_thread": False, "timeout": 15},
            "pool_pre_ping": True,
            "pool_size": 3,
            "max_overflow": 5,
            "pool_recycle": 120,
        }
    else:
        sqlite_kwargs = {
            "connect_args": {"check_same_thread": False, "timeout": 30},
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 600,
        }

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
        # Performance: larger in-memory cache (8MB) and memory-mapped I/O (256MB)
        cursor.execute("PRAGMA cache_size=-8000")
        cursor.execute("PRAGMA mmap_size=268435456")
        # Avoid unnecessary temp file I/O
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
else:
    # -----------------------------------------------------------------------
    # PostgreSQL / other: production-grade pool config
    # -----------------------------------------------------------------------
    pg_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if _is_serverless_runtime():
        # Serverless: small pool, short recycle for cold-start efficiency
        pg_kwargs.update({
            "pool_size": 3,
            "max_overflow": 5,
        })
    else:
        pg_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        })

    engine = create_engine(DB_URL, **pg_kwargs)
    logger.info("Using PostgreSQL database: %s", DB_URL.split("@")[-1] if "@" in DB_URL else "(local)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
