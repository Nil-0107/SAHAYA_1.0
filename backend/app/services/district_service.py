"""District Officer scope-limited dashboard service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_assignment import AssignmentType, CaseAssignment
from app.models.notification import Notification
from app.models.support_request import SupportRequest, SupportRequestStatus, SupportRequestType
from app.models.user import User


class DistrictDashboardService:
    def __init__(self, database: Session, *, include_demo: bool = True) -> None:
        self.database = database
        self.include_demo = include_demo

    def dashboard(self, *, user: User) -> dict[str, list | int]:
        scope_conditions = []
        if user.district_id is not None:
            scope_conditions.append(User.district_id == user.district_id)
        case_query = select(Case.id).join(CaseAssignment, CaseAssignment.case_id == Case.id).join(User, User.id == Case.owner_user_id).where(
            CaseAssignment.assignee_user_id == user.id,
            CaseAssignment.assignment_type == AssignmentType.DISTRICT_COORDINATION,
            CaseAssignment.active.is_(True),
            *scope_conditions,
        )
        if not self.include_demo:
            case_query = case_query.where(
                Case.is_demo.is_(False), CaseAssignment.is_demo.is_(False)
            )
        case_ids = list(
            self.database.scalars(
                case_query
                .distinct()
            )
        )
        if not case_ids:
            return {
                "cases": [],
                "assistance_requests": [],
                "coordination": [],
                "case_updates": [],
                "notifications": [],
                "aggregate": {
                    "authorized_case_count": 0,
                    "open_assistance_request_count": 0,
                    "active_coordination_count": 0,
                    "protection_request_count": 0,
                    "unread_notification_count": 0,
                },
            }

        case_data_query = select(Case).where(Case.id.in_(case_ids))
        request_query = select(SupportRequest).where(SupportRequest.case_id.in_(case_ids))
        coordination_query = select(CaseAssignment).where(
                    CaseAssignment.case_id.in_(case_ids),
                    CaseAssignment.assignee_user_id == user.id,
                    CaseAssignment.assignment_type == AssignmentType.DISTRICT_COORDINATION,
                    CaseAssignment.active.is_(True),
                )
        if not self.include_demo:
            case_data_query = case_data_query.where(Case.is_demo.is_(False))
            request_query = request_query.where(SupportRequest.is_demo.is_(False))
            coordination_query = coordination_query.where(CaseAssignment.is_demo.is_(False))
        cases = list(self.database.scalars(case_data_query.order_by(Case.created_at.desc(), Case.id.desc())))
        assistance_requests = list(self.database.scalars(request_query.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())))
        coordination = list(self.database.scalars(coordination_query.order_by(CaseAssignment.assigned_at.desc(), CaseAssignment.id.desc())))
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
            "cases": cases,
            "assistance_requests": assistance_requests,
            "coordination": coordination,
            "case_updates": notifications,
            "notifications": notifications,
            "aggregate": {
                "authorized_case_count": len(cases),
                "open_assistance_request_count": sum(
                    request.status not in {SupportRequestStatus.RESOLVED, SupportRequestStatus.CANCELLED}
                    for request in assistance_requests
                ),
                "active_coordination_count": len(coordination),
                "protection_request_count": sum(
                    request.type == SupportRequestType.PROTECTION
                    and request.status not in {SupportRequestStatus.RESOLVED, SupportRequestStatus.CANCELLED}
                    for request in assistance_requests
                ),
                "unread_notification_count": sum(not notification.is_read for notification in notifications),
            },
        }
