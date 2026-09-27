"""Role- and geography-scoped case assignment and support actions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_assignment import AssignmentStatus, AssignmentType, CaseAssignment
from app.models.notification import Notification
from app.models.support_action import SupportAction
from app.models.support_request import SupportRequest, SupportRequestStatus
from app.models.user import Role, User


class AssignmentServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AssignmentService:
    def __init__(self, database: Session) -> None:
        self.database = database

    def create_assignment(
        self,
        *,
        actor: User,
        support_request_id: int,
        assignee_user_id: int,
        assignment_type: AssignmentType,
        reason: str,
    ) -> CaseAssignment:
        request = self.database.get(SupportRequest, support_request_id)
        if request is None:
            raise AssignmentServiceError(404, "SUPPORT_REQUEST_NOT_FOUND", "Support request not found")
        case = self.database.get(Case, request.case_id)
        assignee = self.database.get(User, assignee_user_id)
        if case is None or assignee is None:
            raise AssignmentServiceError(404, "ASSIGNMENT_TARGET_NOT_FOUND", "Assignment target not found")
        self._validate_assignment_scope(actor=actor, case=case, assignee=assignee, assignment_type=assignment_type)
        existing = self.database.scalar(
            select(CaseAssignment).where(
                CaseAssignment.support_request_id == request.id,
                CaseAssignment.assignee_user_id == assignee.id,
                CaseAssignment.assignment_type == assignment_type,
                CaseAssignment.active.is_(True),
            )
        )
        if existing is not None:
            raise AssignmentServiceError(409, "ASSIGNMENT_ALREADY_EXISTS", "This account is already assigned")
        assignment = CaseAssignment(
            case_id=case.id,
            support_request_id=request.id,
            assignee_user_id=assignee.id,
            assigned_by_user_id=actor.id,
            assignment_type=assignment_type,
            status=AssignmentStatus.ACTIVE,
            reason=reason.strip(),
            active=True,
        )
        request.status = SupportRequestStatus.ASSIGNED
        self.database.add(assignment)
        self.database.flush()
        self.database.add(
            Notification(
                user_id=assignee.id,
                case_id=case.id,
                type="support_assignment",
                title="New assigned support request",
                message="A support request has been assigned to your authorised account.",
            )
        )
        self.database.add(
            AuditLog(
                actor_user_id=actor.id,
                action="CASE_ASSIGNMENT_CREATED",
                resource_type="support_request",
                resource_id=str(request.id),
                metadata_json={
                    "assignment_id": str(assignment.id),
                    "assignment_type": assignment_type.value,
                    "assignee_user_id": str(assignee.id),
                },
            )
        )
        self.database.commit()
        self.database.refresh(assignment)
        return assignment

    def list_assignments(self, *, actor: User, case_id: int) -> list[CaseAssignment]:
        case = self.database.get(Case, case_id)
        if case is None:
            raise AssignmentServiceError(404, "CASE_NOT_FOUND", "Case not found")
        query = select(CaseAssignment).where(CaseAssignment.case_id == case.id)
        if actor.role == Role.VICTIM:
            if case.owner_user_id != actor.id:
                raise AssignmentServiceError(404, "CASE_NOT_FOUND", "Case not found")
        elif actor.role == Role.COUNSELLOR:
            query = query.where(CaseAssignment.assignee_user_id == actor.id)
        elif actor.role == Role.DISTRICT_ADMIN:
            if actor.district_id is not None:
                owner = self.database.get(User, case.owner_user_id)
                if owner is None or owner.district_id != actor.district_id:
                    raise AssignmentServiceError(404, "CASE_NOT_FOUND", "Case not found")
        elif actor.role in {Role.STATE_ADMIN, Role.NATIONAL_ADMIN}:
            if actor.role == Role.STATE_ADMIN and actor.state_id is not None:
                owner = self.database.get(User, case.owner_user_id)
                if owner is None or owner.state_id != actor.state_id:
                    raise AssignmentServiceError(404, "CASE_NOT_FOUND", "Case not found")
        else:
            raise AssignmentServiceError(403, "ROLE_FORBIDDEN", "Case role is not allowed")
        return list(self.database.scalars(query.order_by(CaseAssignment.assigned_at.desc(), CaseAssignment.id.desc())))

    def add_support_action(
        self,
        *,
        actor: User,
        support_request_id: int,
        action: str,
        notes: str,
        status,
        request_status: SupportRequestStatus | None,
    ) -> SupportAction:
        request = self.database.get(SupportRequest, support_request_id)
        if request is None:
            raise AssignmentServiceError(404, "SUPPORT_REQUEST_NOT_FOUND", "Support request not found")
        if not self._has_active_assignment(actor=actor, request=request):
            raise AssignmentServiceError(403, "SUPPORT_ACTION_FORBIDDEN", "You are not assigned to this support request")
        if request_status is not None:
            if request_status == SupportRequestStatus.PENDING:
                raise AssignmentServiceError(422, "SUPPORT_STATUS_INVALID", "Assigned support cannot return to pending")
            request.status = request_status
            if request_status == SupportRequestStatus.RESOLVED:
                request.resolved_at = request.resolved_at or datetime.now(timezone.utc)
        support_action = SupportAction(
            support_request_id=request.id,
            actor_user_id=actor.id,
            action=action.strip(),
            status=status,
            notes=notes.strip(),
        )
        self.database.add(support_action)
        self.database.flush()
        self.database.add(
            AuditLog(
                actor_user_id=actor.id,
                action="SUPPORT_ACTION_RECORDED",
                resource_type="support_request",
                resource_id=str(request.id),
                metadata_json={"action_id": str(support_action.id), "request_status": request.status.value},
            )
        )
        self.database.commit()
        self.database.refresh(support_action)
        return support_action

    def _has_active_assignment(self, *, actor: User, request: SupportRequest) -> bool:
        assignment = self.database.scalar(
            select(CaseAssignment).where(
                CaseAssignment.support_request_id == request.id,
                CaseAssignment.assignee_user_id == actor.id,
                CaseAssignment.active.is_(True),
            )
        )
        if assignment is None:
            return False
        if actor.district_id is not None:
            owner = self.database.get(User, request.user_id)
            return owner is not None and owner.district_id == actor.district_id
        return True

    def _validate_assignment_scope(
        self,
        *,
        actor: User,
        case: Case,
        assignee: User,
        assignment_type: AssignmentType,
    ) -> None:
        owner = self.database.get(User, case.owner_user_id)
        if owner is None:
            raise AssignmentServiceError(422, "CASE_OWNER_NOT_FOUND", "Case owner is not available")
        if assignment_type == AssignmentType.WELLBEING_COUNSELLOR:
            if actor.role != Role.DISTRICT_ADMIN or assignee.role != Role.COUNSELLOR:
                raise AssignmentServiceError(403, "ASSIGNMENT_ROLE_FORBIDDEN", "Only a District Administrator can appoint a counsellor")
            if actor.district_id is None or assignee.district_id != actor.district_id or owner.district_id != actor.district_id:
                raise AssignmentServiceError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "Counsellor assignment must remain within the administrator's district")
        elif assignment_type == AssignmentType.DISTRICT_COORDINATION:
            if assignee.role != Role.DISTRICT_ADMIN:
                raise AssignmentServiceError(403, "ASSIGNMENT_ROLE_FORBIDDEN", "District coordination requires a District Administrator")
            if actor.role == Role.STATE_ADMIN and (actor.state_id is None or assignee.state_id != actor.state_id or owner.state_id != actor.state_id):
                raise AssignmentServiceError(403, "GEOGRAPHIC_SCOPE_FORBIDDEN", "District assignment must remain within the administrator's state")
            if actor.role == Role.NATIONAL_ADMIN:
                return
            raise AssignmentServiceError(403, "ASSIGNMENT_ROLE_FORBIDDEN", "Role cannot create this assignment")
        else:
            raise AssignmentServiceError(422, "ASSIGNMENT_TYPE_INVALID", "Unsupported assignment type")
