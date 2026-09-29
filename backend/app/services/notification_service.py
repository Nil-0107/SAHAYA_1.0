"""Owner-scoped notification service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, true, update
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.user import User


class NotificationServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class NotificationService:
    def __init__(self, database: Session, *, include_demo: bool = True) -> None:
        self.database = database
        self.include_demo = include_demo

    def _scope(self):
        return true() if self.include_demo else Notification.is_demo.is_(False)

    def list_for_user(self, *, user: User) -> list[Notification]:
        return list(
            self.database.scalars(
                select(Notification)
                .where(Notification.user_id == user.id, self._scope())
                .order_by(Notification.created_at.desc(), Notification.id.desc())
            )
        )

    def mark_read(self, *, user: User, notification_id: int) -> Notification:
        notification = self.database.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
                self._scope(),
            )
        )
        if notification is None:
            raise NotificationServiceError(404, "NOTIFICATION_NOT_FOUND", "Notification not found")
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            self.database.add(
                AuditLog(
                    actor_user_id=user.id,
                    action="NOTIFICATION_READ",
                    resource_type="notification",
                    resource_id=str(notification.id),
                    metadata_json={},
                )
            )
            self.database.commit()
            self.database.refresh(notification)
        return notification

    def mark_all_read(self, *, user: User) -> int:
        result = self.database.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False), self._scope())
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        self.database.add(
            AuditLog(
                actor_user_id=user.id,
                action="NOTIFICATIONS_READ_ALL",
                resource_type="notification",
                resource_id="inbox",
                metadata_json={"updated_count": int(result.rowcount or 0)},
            )
        )
        self.database.commit()
        return int(result.rowcount or 0)
