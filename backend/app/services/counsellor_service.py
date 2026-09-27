"""Counsellor assignment-scoped dashboard service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_assignment import AssignmentType, CaseAssignment
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.checkin import Checkin
from app.models.support_action import SupportAction
from app.models.support_request import SupportRequest, SupportRequestStatus, SupportRequestType
from app.models.user import User


class CounsellorDashboardService:
    def __init__(self, database: Session) -> None:
        self.database = database

    def assigned_users(self, *, user: User) -> list[dict]:
        rows = self.database.execute(
            select(SupportRequest, Case, User, Profile)
            .join(Case, Case.id == SupportRequest.case_id)
            .join(User, User.id == SupportRequest.user_id)
            .join(Profile, Profile.user_id == User.id)
            .join(CaseAssignment, CaseAssignment.support_request_id == SupportRequest.id)
            .where(
                CaseAssignment.assignee_user_id == user.id,
                CaseAssignment.assignment_type == AssignmentType.WELLBEING_COUNSELLOR,
                CaseAssignment.active.is_(True),
            )
            .order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())
        ).all()
        result = []
        seen = set()
        for request, case, victim, profile in rows:
            key = (victim.id, case.id, request.id)
            if key in seen:
                continue
            seen.add(key)
            last_checkin = self.database.scalar(select(Checkin.created_at).where(Checkin.user_id == victim.id).order_by(Checkin.created_at.desc()).limit(1))
            result.append({
                "id": victim.id, "full_name": profile.full_name, "display_name": profile.display_name,
                "email": victim.email, "phone": victim.phone, "date_of_birth": victim.date_of_birth,
                "district_name": victim.district_unit.name if victim.district_unit else None,
                "case_id": case.id, "case_number": case.case_number,
                "support_request_id": request.id, "support_category": request.type.value,
                "support_status": request.status, "last_checkin_at": last_checkin, "is_demo": victim.is_demo,
            })
        return result

    def dashboard(self, *, user: User) -> dict[str, list | int]:
        assignment_query = select(CaseAssignment).where(
            CaseAssignment.assignee_user_id == user.id,
            CaseAssignment.assignment_type == AssignmentType.WELLBEING_COUNSELLOR,
            CaseAssignment.active.is_(True),
        )
        if user.district_id is not None:
            assignment_query = assignment_query.join(Case, Case.id == CaseAssignment.case_id).join(
                User, User.id == Case.owner_user_id
            ).where(User.district_id == user.district_id)
        assignments = list(
            self.database.scalars(
                assignment_query.order_by(CaseAssignment.assigned_at.desc(), CaseAssignment.id.desc())
            )
        )
        request_ids = [assignment.support_request_id for assignment in assignments]
        case_ids = [assignment.case_id for assignment in assignments]
        if not request_ids:
            return {
                "support_requests": [],
                "follow_ups": [],
                "support_actions": [],
                "notifications": [],
                "aggregate": {
                    "assigned_request_count": 0,
                    "open_follow_up_count": 0,
                    "support_action_count": 0,
                    "resolved_request_count": 0,
                    "unread_notification_count": 0,
                },
            }

        requests = list(
            self.database.scalars(
                select(SupportRequest)
                .where(SupportRequest.id.in_(request_ids))
                .order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())
            )
        )
        actions = list(
            self.database.scalars(
                select(SupportAction)
                .where(
                    SupportAction.support_request_id.in_(request_ids),
                    SupportAction.actor_user_id == user.id,
                )
                .order_by(SupportAction.created_at.desc(), SupportAction.id.desc())
            )
        )
        notifications = list(
            self.database.scalars(
                select(Notification)
                .where(
                    Notification.user_id == user.id,
                    Notification.case_id.in_(case_ids),
                )
                .order_by(Notification.created_at.desc(), Notification.id.desc())
            )
        )
        return {
            "support_requests": requests,
            "follow_ups": actions,
            "support_actions": actions,
            "notifications": notifications,
            "aggregate": {
                "assigned_request_count": len(requests),
                "open_follow_up_count": sum(
                    request.type == SupportRequestType.WELLBEING
                    and request.status not in {SupportRequestStatus.RESOLVED, SupportRequestStatus.CANCELLED}
                    for request in requests
                ),
                "support_action_count": len(actions),
                "resolved_request_count": sum(request.status == SupportRequestStatus.RESOLVED for request in requests),
                "unread_notification_count": sum(not notification.is_read for notification in notifications),
            },
        }
