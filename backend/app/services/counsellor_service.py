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
    def __init__(self, database: Session, *, include_demo: bool = True) -> None:
        self.database = database
        self.include_demo = include_demo

    def assigned_users(self, *, user: User) -> list[dict]:
        query = (select(SupportRequest, Case, User, Profile)
            .join(Case, Case.id == SupportRequest.case_id)
            .join(User, User.id == SupportRequest.user_id)
            .join(Profile, Profile.user_id == User.id)
            .join(CaseAssignment, CaseAssignment.support_request_id == SupportRequest.id)
            .where(
                CaseAssignment.assignee_user_id == user.id,
                CaseAssignment.assignment_type == AssignmentType.WELLBEING_COUNSELLOR,
                CaseAssignment.active.is_(True),
            )
        )
        if not self.include_demo:
            query = query.where(
                SupportRequest.is_demo.is_(False),
                Case.is_demo.is_(False),
                User.is_demo.is_(False),
                CaseAssignment.is_demo.is_(False),
            )
        rows = self.database.execute(
            query.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())
        ).all()
        result = []
        seen = set()
        for request, case, victim, profile in rows:
            key = (victim.id, case.id, request.id)
            if key in seen:
                continue
            seen.add(key)
            checkin_query = select(Checkin.created_at).where(Checkin.user_id == victim.id)
            if not self.include_demo:
                checkin_query = checkin_query.where(Checkin.is_demo.is_(False))
            last_checkin = self.database.scalar(checkin_query.order_by(Checkin.created_at.desc()).limit(1))
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
        assignment_query = select(CaseAssignment).join(Case, Case.id == CaseAssignment.case_id).join(
            User, User.id == Case.owner_user_id
        ).where(
            CaseAssignment.assignee_user_id == user.id,
            CaseAssignment.assignment_type == AssignmentType.WELLBEING_COUNSELLOR,
            CaseAssignment.active.is_(True),
        )
        if user.district_id is not None:
            assignment_query = assignment_query.where(User.district_id == user.district_id)
        if not self.include_demo:
            assignment_query = assignment_query.where(
                CaseAssignment.is_demo.is_(False), Case.is_demo.is_(False), User.is_demo.is_(False)
            )
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

        request_query = select(SupportRequest).where(SupportRequest.id.in_(request_ids))
        if not self.include_demo:
            request_query = request_query.where(SupportRequest.is_demo.is_(False))
        requests = list(self.database.scalars(request_query.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())))
        actions = list(
            self.database.scalars(
                select(SupportAction)
                .where(
                    SupportAction.support_request_id.in_(request_ids),
                    SupportAction.actor_user_id == user.id,
                    *(() if self.include_demo else (SupportAction.is_demo.is_(False),)),
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
                    *(() if self.include_demo else (Notification.is_demo.is_(False),)),
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
