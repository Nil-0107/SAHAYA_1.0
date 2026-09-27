"""SQLAlchemy model registry.

Importing this package registers every table, relationship, constraint, and
index on ``Base.metadata``.
"""

from sqlalchemy import Index

from app.models.administrative_unit import AdministrativeUnit

from app.models.ai_conversation import AIConversation, AIConversationStatus
from app.models.ai_message import AIMessage, AIMessageRole, AIMessageStatus
from app.models.audit_log import AuditLog
from app.models.case import Case, CaseStatus
from app.models.case_assignment import AssignmentStatus, AssignmentType, CaseAssignment
from app.models.case_document import CaseDocument, DocumentStatus
from app.models.checkin import Checkin, CheckinAnalysisStatus
from app.models.notification import Notification
from app.models.profile import Profile
from app.models.support_action import SupportAction, SupportActionStatus
from app.models.support_request import (
    SupportRequest,
    SupportRequestStatus,
    SupportRequestType,
)
from app.models.user import Role, User, UserStatus

# Composite indexes support the authorization/dashboard query patterns.
Index("ix_cases_owner_status", Case.owner_user_id, Case.status)
Index("ix_case_documents_case_status", CaseDocument.case_id, CaseDocument.status)
Index("ix_checkins_user_created", Checkin.user_id, Checkin.created_at)
Index("ix_support_requests_case_status", SupportRequest.case_id, SupportRequest.status)
Index("ix_case_assignments_assignee_status", CaseAssignment.assignee_user_id, CaseAssignment.status)
Index("ix_notifications_user_read_created", Notification.user_id, Notification.is_read, Notification.created_at)
Index("ix_audit_resource_created", AuditLog.resource_type, AuditLog.resource_id, AuditLog.created_at)

DEMO_MANAGED_MODELS = (
    AdministrativeUnit,
    User,
    Profile,
    Case,
    CaseDocument,
    Checkin,
    SupportRequest,
    CaseAssignment,
    SupportAction,
    Notification,
    AuditLog,
)

__all__ = (
    "AdministrativeUnit",
    "AIConversation",
    "AIConversationStatus",
    "AIMessage",
    "AIMessageRole",
    "AIMessageStatus",
    "AssignmentStatus",
    "AssignmentType",
    "AuditLog",
    "Case",
    "CaseAssignment",
    "CaseDocument",
    "CaseStatus",
    "Checkin",
    "CheckinAnalysisStatus",
    "DEMO_MANAGED_MODELS",
    "DocumentStatus",
    "Notification",
    "Profile",
    "Role",
    "SupportAction",
    "SupportActionStatus",
    "SupportRequest",
    "SupportRequestStatus",
    "SupportRequestType",
    "User",
    "UserStatus",
)
