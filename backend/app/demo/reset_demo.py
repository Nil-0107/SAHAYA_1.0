"""Controlled removal of synthetic demo rows.

This is a local module command only. It refuses production environments and
uses ``is_demo`` so non-demo records cannot be selected.
"""

from __future__ import annotations

import os

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import ALLOWED_DEMO_ENVIRONMENTS, DemoSeedEnvironmentError, get_settings
from app.db.database import session_scope
from app.models import (
    AuditLog,
    Case,
    CaseAssignment,
    CaseDocument,
    Checkin,
    Notification,
    Profile,
    SupportAction,
    SupportRequest,
    User,
)


# Reverse dependency order for foreign keys.
RESET_ORDER = (
    AuditLog,
    Notification,
    SupportAction,
    CaseAssignment,
    SupportRequest,
    Checkin,
    CaseDocument,
    Case,
    Profile,
    User,
)


def reset_demo(database: Session | None = None) -> dict[str, int]:
    raw_environment = os.getenv("SAATHI_ENV", "").strip().lower()
    if raw_environment not in ALLOWED_DEMO_ENVIRONMENTS:
        raise DemoSeedEnvironmentError(
            "Demo reset is blocked unless SAATHI_ENV is development, local, or test."
        )
    settings = get_settings()
    settings.require_demo_seed_allowed()
    settings.reject_obvious_production_database()
    counts: dict[str, int] = {}
    with session_scope(database) as active_database:
        for model in RESET_ORDER:
            result = active_database.execute(
                delete(model).where(model.is_demo.is_(True))
            )
            counts[model.__tablename__] = int(result.rowcount or 0)
    return counts


def main() -> None:
    try:
        counts = reset_demo()
    except Exception as exc:
        raise SystemExit(f"Demo reset refused: {exc}") from exc
    print("SAATHI synthetic demo records removed from the local database.")
    for table, count in counts.items():
        if count:
            print(f"{table}: {count}")


if __name__ == "__main__":
    main()
