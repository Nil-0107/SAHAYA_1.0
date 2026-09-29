"""Explicit database initialization helper.

This module is never called automatically by application startup or the demo
seed unless a caller explicitly invokes ``initialize_database``.
"""

from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.database import engine
import app.models  # noqa: F401 - registers model metadata


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "date_of_birth" not in columns and str(engine.url).startswith("sqlite"):
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN date_of_birth DATE"))
    if "checkins" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("checkins")}
        if "emotion_result" not in columns and str(engine.url).startswith("sqlite"):
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE checkins ADD COLUMN emotion_result JSON"))
