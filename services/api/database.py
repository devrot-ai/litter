from __future__ import annotations

import os

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DB_URL = os.getenv("LITTER_DB_URL", "sqlite:///./litter_events.db")

if DB_URL.startswith("sqlite"):
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_size=40,
        max_overflow=80,
        pool_timeout=30,
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
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
