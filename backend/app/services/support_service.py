"""Role-scoped human support request service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_assignment import CaseAssignment
from app.models.support_request import SupportRequest, SupportRequestStatus, SupportRequestType
from app.models.user import Role, User
from app.models.notification import Notification
from app.schemas.support import SupportCategory
from app.services.priority_service import PriorityService


class SupportServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class SupportService:
    _category_types = {
        SupportCategory.COUNSELLING: SupportRequestType.WELLBEING,
        SupportCategory.LEGAL_HELP: SupportRequestType.LEGAL,
        SupportCategory.PROTECTION_RELOCATION: SupportRequestType.PROTECTION,
    }

    def __init__(self, database: Session) -> None:
        self.database = database

    def create(self, *, user: User, case_id: int, category: SupportCategory, details: str) -> SupportRequest:
        if user.role != Role.VICTIM:
            raise SupportServiceError(403, "SUPPORT_REQUEST_FORBIDDEN", "Only Victim / User accounts can create support requests")
        case = self.database.scalar(
            select(Case).where(Case.id == case_id, Case.owner_user_id == user.id)
        )
        if case is None:
            raise SupportServiceError(404, "CASE_NOT_FOUND", "Case not found")
        request_type = self._category_types[category]
        if request_type == SupportRequestType.PROTECTION:
            case.protection_request_open = True
        priority_service = PriorityService()
        priority = priority_service.calculate(
            verified_high_priority_category=priority_service.is_verified_high_priority_category(
                category=case.category,
                category_verified=case.category_verified,
            ),
            open_protection_request=case.protection_request_open,
            explicit_human_support_request=True,
            verified_wellbeing_review_flag=case.wellbeing_review_verified,
        ).priority.value.casefold()
        request = SupportRequest(
            user_id=user.id,
            case_id=case.id,
            type=request_type,
            status=SupportRequestStatus.PENDING,
            priority=priority,
            explicit_human_request=True,
            details=details.strip(),
        )
        if not request.details:
            raise SupportServiceError(422, "SUPPORT_REQUEST_INVALID", "Support request details must not be empty")
        self.database.add(request)
        try:
            self.database.flush()
            self.database.add(
                AuditLog(
                    actor_user_id=user.id,
                    action="SUPPORT_REQUEST_CREATED",
                    resource_type="support_request",
                    resource_id=str(request.id),
                    metadata_json={"category": category.value, "case_id": str(case.id)},
                )
            )
            # Notify the authorised administrative hierarchy immediately. Counsellors receive it after assignment.
            recipients = list(self.database.scalars(select(User).where(User.id != user.id)))
            for recipient in recipients:
                in_scope = (
                    recipient.role == Role.NATIONAL_ADMIN
                    or (recipient.role == Role.STATE_ADMIN and user.state_id is not None and recipient.state_id == user.state_id)
                    or (recipient.role == Role.DISTRICT_ADMIN and user.district_id is not None and recipient.district_id == user.district_id)
                )
                if in_scope:
                    self.database.add(Notification(user_id=recipient.id, case_id=case.id, type="support_request", title="New support request", message=f"A {category.value.replace('_', ' ')} support request was submitted for case {case.case_number}. Review it in your authorised dashboard."))
            self.database.add(Notification(user_id=user.id, case_id=case.id, type="support_request", title="Support request received", message="Your human support request was saved and routed to the authorised support workflow."))
            self.database.commit()
            self.database.refresh(request)
            return request
        except Exception:
            self.database.rollback()
            raise SupportServiceError(503, "SUPPORT_REQUEST_SAVE_FAILED", "The support request could not be saved")

    def list_for_user(self, *, user: User) -> list[SupportRequest]:
        query = select(SupportRequest)
        if user.role == Role.VICTIM:
            query = query.where(SupportRequest.user_id == user.id)
        elif user.role in {Role.COUNSELLOR, Role.DISTRICT_ADMIN}:
            query = query.join(
                CaseAssignment,
                CaseAssignment.support_request_id == SupportRequest.id,
            ).join(Case, Case.id == CaseAssignment.case_id).join(User, User.id == Case.owner_user_id).where(
                CaseAssignment.assignee_user_id == user.id,
                CaseAssignment.active.is_(True),
            )
            if user.district_id is not None:
                query = query.where(User.district_id == user.district_id)
            query = query.distinct()
        elif user.role in {Role.STATE_ADMIN, Role.NATIONAL_ADMIN}:
            # Administrative dashboards use aggregate queries. Raw support
            # content is not exposed through the generic support endpoint.
            return []
        else:
            return []
        return list(self.database.scalars(query.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())))

    def get_for_user(self, *, user: User, request_id: int) -> SupportRequest:
        request = self.database.scalar(
            select(SupportRequest).where(
                SupportRequest.id == request_id,
                *self._access_conditions(user),
            )
        )
        if request is None:
            raise SupportServiceError(404, "SUPPORT_REQUEST_NOT_FOUND", "Support request not found")
        return request

    def _access_conditions(self, user: User) -> tuple:
        if user.role == Role.VICTIM:
            return (SupportRequest.user_id == user.id,)
        if user.role in {Role.COUNSELLOR, Role.DISTRICT_ADMIN}:
            assignment_scope = select(CaseAssignment.support_request_id).join(
                Case, Case.id == CaseAssignment.case_id
            ).join(User, User.id == Case.owner_user_id).where(
                CaseAssignment.assignee_user_id == user.id,
                CaseAssignment.active.is_(True),
            )
            if user.district_id is not None:
                assignment_scope = assignment_scope.where(User.district_id == user.district_id)
            return (SupportRequest.id.in_(assignment_scope),)
        if user.role in {Role.STATE_ADMIN, Role.NATIONAL_ADMIN}:
            return (SupportRequest.id < 0,)
        return (SupportRequest.id < 0,)
