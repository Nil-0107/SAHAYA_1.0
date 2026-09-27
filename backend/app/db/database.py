"""SQLAlchemy database setup.

Models are declared here so existing SQLAlchemy/FastAPI modules can continue
to use ``Base`` without coupling the controlled seed to startup behaviour.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base


__all__ = ("Base", "SessionLocal", "create_database_engine", "engine", "get_db", "session_scope")


def create_database_engine(database_url: str | None = None) -> Engine:
    resolved_url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    engine = create_engine(resolved_url, connect_args=connect_args)

    if resolved_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency used by the real authentication/API layer."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@contextmanager
def session_scope(database: Session | None = None) -> Generator[Session, None, None]:
    """Provide a transaction and never leave a partially seeded database.

    A caller-supplied session uses a savepoint, so a seed failure cannot leave
    partial changes in that caller's surrounding transaction. The caller still
    controls the final outer commit.
    """
    owns_session = database is None
    active_session = database or SessionLocal()
    transaction = active_session.begin() if owns_session else active_session.begin_nested()
    try:
        yield active_session
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        if owns_session:
            active_session.close()
