"""Remove synthetic application records while preserving test-login accounts."""

from __future__ import annotations

import os

from sqlalchemy import delete

from app.core.config import ALLOWED_DEMO_ENVIRONMENTS, DemoSeedEnvironmentError, get_settings
from app.db.database import session_scope
from app.models import AuditLog, Case, CaseAssignment, CaseDocument, Checkin, Notification, SupportAction, SupportRequest


APPLICATION_MODELS = (
    AuditLog,
    Notification,
    SupportAction,
    CaseAssignment,
    SupportRequest,
    Checkin,
    CaseDocument,
    Case,
)


def reset_demo_application(database=None) -> dict[str, int]:
    if os.getenv("SAHAYA_ENV", "").strip().lower() not in ALLOWED_DEMO_ENVIRONMENTS:
        raise DemoSeedEnvironmentError("Demo application reset is blocked outside development, local, or test.")
    settings = get_settings()
    settings.require_demo_seed_allowed()
    settings.reject_obvious_production_database()
    counts: dict[str, int] = {}
    with session_scope(database) as active_database:
        for model in APPLICATION_MODELS:
            result = active_database.execute(delete(model).where(model.is_demo.is_(True)))
            counts[model.__tablename__] = int(result.rowcount or 0)
    return counts


if __name__ == "__main__":
    print(reset_demo_application())
