"""Administrator aggregate dashboard service.

The administrator dashboard reads operational tables directly, but deliberately
returns counts and de-identified operational references rather than victim
profiles, names, contact details, or support-request free text.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.case import Case, CaseStatus
from app.models.case_assignment import CaseAssignment
from app.models.checkin import Checkin
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.support_request import SupportRequest, SupportRequestStatus
from app.models.user import Role, User
from app.services.priority_service import PriorityService


_OPEN_CASE_STATUSES = {CaseStatus.OPEN.value, CaseStatus.IN_PROGRESS.value, CaseStatus.ON_HOLD.value}
_OPEN_REQUEST_STATUSES = {
    SupportRequestStatus.PENDING.value,
    SupportRequestStatus.ASSIGNED.value,
    SupportRequestStatus.IN_PROGRESS.value,
}
_ESCALATED_PRIORITIES = {"high", "urgent", "critical", "elevated"}


class AdminDashboardService:
    def __init__(self, database: Session) -> None:
        self.database = database
        self.priority_service = PriorityService()

    def user_directory(self, *, user: User, include_demo: bool = False) -> list[dict[str, Any]]:
        scope = [User.role == Role.VICTIM]
        if user.role == Role.STATE_ADMIN:
            scope.append(User.state_id == user.state_id)
        elif user.role == Role.DISTRICT_ADMIN:
            scope.append(User.district_id == user.district_id)
        elif user.role != Role.NATIONAL_ADMIN:
            return []
        user_query = select(User).join(Profile, Profile.user_id == User.id).where(*scope)
        if not include_demo:
            user_query = user_query.where(User.is_demo.is_(False))
        rows = self.database.scalars(user_query.order_by(User.created_at.desc(), User.id.desc())).all()
        result = []
        for account in rows:
            cases = list(self.database.scalars(select(Case).where(Case.owner_user_id == account.id)))
            supports = list(self.database.scalars(select(SupportRequest).where(SupportRequest.user_id == account.id)))
            last_checkin = self.database.scalar(select(Checkin.created_at).where(Checkin.user_id == account.id).order_by(Checkin.created_at.desc()).limit(1))
            result.append({
                "id": account.id,
                "full_name": account.profile.full_name,
                "display_name": account.profile.display_name,
                "email": account.email,
                "phone": account.phone,
                "date_of_birth": account.date_of_birth,
                "role": account.role.value,
                "status": account.status.value,
                "state_id": account.state_id,
                "district_id": account.district_id,
                "state_name": account.state_unit.name if account.state_unit else None,
                "district_name": account.district_unit.name if account.district_unit else None,
                "case_count": len(cases),
                "open_case_count": sum(case.status.value in {"open", "in_progress", "on_hold"} for case in cases),
                "support_request_count": len(supports),
                "last_checkin_at": last_checkin,
                "is_demo": account.is_demo,
            })
        return result

    def dashboard(self, *, user: User, include_demo: bool = False) -> dict[str, Any]:
        scope_conditions = []
        if user.role == Role.STATE_ADMIN:
            scope_conditions.append(User.state_id == user.state_id)
        elif user.role == Role.DISTRICT_ADMIN:
            scope_conditions.append(User.district_id == user.district_id)
        if not include_demo:
            scope_conditions.append(User.is_demo.is_(False))
        case_rows = self.database.execute(
            select(
                Case.id.label("case_id"),
                Case.case_number.label("case_number"),
                Profile.city_or_district.label("district"),
                Case.status.label("case_status"),
                Case.is_demo.label("case_is_demo"),
            )
            .join(User, User.id == Case.owner_user_id)
            .join(Profile, Profile.user_id == User.id)
            .where(*scope_conditions)
        ).all()
        priority_case_rows = self.database.execute(
            select(
                Case.id.label("case_id"),
                Case.case_number.label("case_number"),
                Profile.city_or_district.label("district"),
                Case.category.label("category"),
                Case.category_verified.label("category_verified"),
                Case.protection_request_open.label("open_protection_request"),
                Case.wellbeing_review_verified.label("wellbeing_review_verified"),
                Case.is_demo.label("case_is_demo"),
            )
            .join(User, User.id == Case.owner_user_id)
            .join(Profile, Profile.user_id == User.id)
            .where(*scope_conditions)
        ).all()
        case_ids = [row.case_id for row in case_rows]
        explicit_support_case_ids = set(
            self.database.scalars(
                select(SupportRequest.case_id).where(
                    SupportRequest.explicit_human_request.is_(True),
                    SupportRequest.case_id.in_(case_ids),
                )
            )
        ) if case_ids else set()
        request_rows = self.database.execute(
            select(
                SupportRequest.id.label("request_id"),
                SupportRequest.case_id.label("case_id"),
                Profile.city_or_district.label("district"),
                SupportRequest.type.label("request_type"),
                SupportRequest.status.label("request_status"),
                SupportRequest.priority.label("priority"),
                SupportRequest.created_at.label("created_at"),
                SupportRequest.is_demo.label("request_is_demo"),
            )
            .join(Case, Case.id == SupportRequest.case_id)
            .join(User, User.id == Case.owner_user_id)
            .join(Profile, Profile.user_id == User.id)
            .where(*scope_conditions)
        ).all()
        assignment_rows = self.database.execute(
            select(
                CaseAssignment.case_id.label("case_id"),
                CaseAssignment.is_demo.label("assignment_is_demo"),
            )
            .join(Case, Case.id == CaseAssignment.case_id)
            .join(User, User.id == Case.owner_user_id)
            .join(Profile, Profile.user_id == User.id)
            .where(CaseAssignment.active.is_(True), *scope_conditions)
        ).all()

        notifications = list(
            self.database.scalars(
                select(Notification)
                .where(Notification.user_id == user.id)
                .order_by(Notification.created_at.desc(), Notification.id.desc())
            )
        )
        if not include_demo:
            notifications = [item for item in notifications if not item.is_demo]
        managed_user_ids = [user.id]
        managed_user_query = select(User.id)
        if user.role == Role.STATE_ADMIN:
            managed_user_query = managed_user_query.where(User.state_id == user.state_id)
        elif user.role == Role.DISTRICT_ADMIN:
            managed_user_query = managed_user_query.where(User.district_id == user.district_id)
        else:
            managed_user_query = managed_user_query.where(User.id == user.id)
        managed_user_ids.extend(self.database.scalars(managed_user_query).all())
        audit_rows = list(
            self.database.scalars(
                select(AuditLog)
                .where(
                    or_(
                        AuditLog.actor_user_id == user.id,
                        AuditLog.resource_id.in_([row.case_number for row in case_rows]),
                        AuditLog.resource_id.in_([str(item) for item in set(managed_user_ids)]),
                    )
                )
                .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
                .limit(200)
            )
        )
        total_checkins = self.database.scalar(
            select(func.count(Checkin.id))
            .join(User, User.id == Checkin.user_id)
            .where(*scope_conditions)
        ) or 0
        total_users = self.database.scalar(
            select(func.count(User.id)).where(*scope_conditions)
        ) or 0
        active_users = self.database.scalar(
            select(func.count(User.id)).where(
                User.is_active.is_(True), User.status == "active", *scope_conditions
            )
        ) or 0

        case_to_district = {row.case_id: row.district for row in case_rows}
        district_states: dict[str, dict[str, Any]] = {}
        for row in case_rows:
            state = district_states.setdefault(
                row.district,
                {
                    "case_ids": set(),
                    "active_case_count": 0,
                    "support_request_count": 0,
                    "open_support_request_count": 0,
                    "high_priority_request_count": 0,
                    "active_assignment_count": 0,
                    "demo_flags": [],
                },
            )
            state["case_ids"].add(row.case_id)
            state["demo_flags"].append(bool(row.case_is_demo))
            if _value(row.case_status) in _OPEN_CASE_STATUSES:
                state["active_case_count"] += 1

        support_by_type: Counter[str] = Counter()
        support_by_status: Counter[str] = Counter()
        escalated_by_date: dict[Any, dict[str, int]] = {}
        for row in request_rows:
            request_type = _value(row.request_type)
            request_status = _value(row.request_status)
            support_by_type[request_type] += 1
            support_by_status[request_status] += 1
            state = district_states.setdefault(
                row.district,
                {
                    "case_ids": set(),
                    "active_case_count": 0,
                    "support_request_count": 0,
                    "open_support_request_count": 0,
                    "high_priority_request_count": 0,
                    "active_assignment_count": 0,
                    "demo_flags": [],
                },
            )
            state["support_request_count"] += 1
            state["demo_flags"].append(bool(row.request_is_demo))
            is_open = request_status in _OPEN_REQUEST_STATUSES
            if is_open:
                state["open_support_request_count"] += 1
            if row.priority.casefold() in _ESCALATED_PRIORITIES:
                state["high_priority_request_count"] += 1
                day = row.created_at.date()
                point = escalated_by_date.setdefault(day, {"request_count": 0, "open_count": 0, "resolved_count": 0})
                point["request_count"] += 1
                if is_open:
                    point["open_count"] += 1
                if request_status == SupportRequestStatus.RESOLVED.value:
                    point["resolved_count"] += 1

        priority_queue: list[dict[str, Any]] = []
        for row in priority_case_rows:
            calculation = self.priority_service.calculate(
                verified_high_priority_category=self.priority_service.is_verified_high_priority_category(
                    category=row.category,
                    category_verified=bool(row.category_verified),
                ),
                open_protection_request=bool(row.open_protection_request),
                explicit_human_support_request=row.case_id in explicit_support_case_ids,
                verified_wellbeing_review_flag=bool(row.wellbeing_review_verified),
            )
            factors = calculation.factors
            priority_queue.append(
                {
                    "case_id": row.case_id,
                    "case_number": row.case_number,
                    "district": row.district,
                    "category": row.category,
                    "category_verified": bool(row.category_verified),
                    "priority": calculation.priority.value,
                    "explanation": calculation.explanation,
                    "reasons": list(calculation.reasons),
                    "factors": {
                        "verified_high_priority_category": factors.verified_high_priority_category,
                        "open_protection_request": factors.open_protection_request,
                        "explicit_human_support_request": factors.explicit_human_support_request,
                        "verified_wellbeing_review_flag": factors.verified_wellbeing_review_flag,
                    },
                    "is_demo": bool(row.case_is_demo),
                }
            )

        for row in assignment_rows:
            district = case_to_district.get(row.case_id)
            if district is None:
                continue
            state = district_states[district]
            state["active_assignment_count"] += 1
            state["demo_flags"].append(bool(row.assignment_is_demo))

        active_case_count = sum(
            _value(row.case_status) in _OPEN_CASE_STATUSES for row in case_rows
        )
        open_request_count = sum(
            _value(row.request_status) in _OPEN_REQUEST_STATUSES for row in request_rows
        )
        active_assignment_count = len(assignment_rows)
        priority_queue.sort(
            key=lambda item: (
                _priority_rank(item["priority"]),
                item["case_id"],
            )
        )
        district_analytics = [
            {
                "district": district,
                "case_count": len(state["case_ids"]),
                "active_case_count": state["active_case_count"],
                "support_request_count": state["support_request_count"],
                "open_support_request_count": state["open_support_request_count"],
                "high_priority_request_count": state["high_priority_request_count"],
                "active_assignment_count": state["active_assignment_count"],
                "is_demo": bool(state["demo_flags"]) and all(state["demo_flags"]),
            }
            for district, state in sorted(district_states.items())
        ]
        escalation_trends = [
            {"date": day, **counts} for day, counts in sorted(escalated_by_date.items())
        ]

        return {
            "aggregate": {
                "total_case_count": len(case_rows),
                "active_case_count": active_case_count,
                "total_support_request_count": len(request_rows),
                "open_support_request_count": open_request_count,
                "resolved_support_request_count": support_by_status.get(SupportRequestStatus.RESOLVED.value, 0),
                "active_assignment_count": active_assignment_count,
                "district_count": len(district_states),
                "total_checkin_count": total_checkins,
                "total_user_count": total_users,
                "active_user_count": active_users,
                "unread_admin_notification_count": sum(not item.is_read for item in notifications),
            },
            "district_analytics": district_analytics,
            "support_request_counts": {
                "by_type": [{"label": label, "count": count} for label, count in sorted(support_by_type.items())],
                "by_status": [{"label": label, "count": count} for label, count in sorted(support_by_status.items())],
            },
            "priority_queue": priority_queue,
            "escalation_trends": escalation_trends,
            "notifications": notifications,
            "audit_entries": [
                {
                    "id": row.id,
                    "actor_user_id": row.actor_user_id,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id if row.resource_id.isdigit() or row.resource_id.startswith("SA-") else "redacted",
                    "metadata": row.metadata_json if isinstance(row.metadata_json, dict) else {},
                    "created_at": row.created_at,
                    "is_demo": row.is_demo,
                }
                for row in audit_rows
            ],
        }


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _priority_rank(priority: str) -> int:
    return {"HIGH": 0, "REVIEW": 1, "STANDARD": 2}.get(priority, 3)
