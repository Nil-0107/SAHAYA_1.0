"""SQLite database foundation, ownership, relationship, and status tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import (
    AIConversation,
    AIConversationStatus,
    AIMessage,
    AIMessageRole,
    AIMessageStatus,
    AssignmentStatus,
    AuditLog,
    Case,
    CaseAssignment,
    CaseDocument,
    CaseStatus,
    Checkin,
    CheckinAnalysisStatus,
    DocumentStatus,
    Notification,
    Profile,
    Role,
    SupportAction,
    SupportActionStatus,
    SupportRequest,
    SupportRequestStatus,
    SupportRequestType,
    User,
    UserStatus,
)


EXPECTED_TABLES = {
    "administrative_units",
    "users",
    "profiles",
    "cases",
    "case_documents",
    "checkins",
    "support_requests",
    "audit_logs",
    "notifications",
    "case_assignments",
    "support_actions",
    "ai_conversations",
    "ai_messages",
}

EXPECTED_COMPOSITE_INDEXES = {
    "ix_cases_owner_status",
    "ix_case_documents_case_status",
    "ix_checkins_user_created",
    "ix_support_requests_case_status",
    "ix_case_assignments_assignee_status",
    "ix_notifications_user_read_created",
    "ix_audit_resource_created",
}


@pytest.fixture
def database() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    active_session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield active_session
    active_session.close()
    engine.dispose()


def _user(
    database: Session,
    *,
    suffix: str,
    role: Role = Role.VICTIM,
    is_demo: bool = False,
    demo_key: str | None = None,
) -> User:
    user = User(
        email=f"{suffix}@example.invalid",
        phone=f"000000{suffix[-4:]}",
        password_hash="scrypt$test$hash",
        role=role,
        status=UserStatus.ACTIVE,
        is_demo=is_demo,
        demo_key=demo_key,
    )
    database.add(user)
    database.flush()
    return user


def test_all_required_tables_indexes_and_demo_constraints_exist(database: Session) -> None:
    inspector = inspect(database.bind)
    assert set(inspector.get_table_names()) == EXPECTED_TABLES

    index_names = {
        index["name"]
        for table_name in EXPECTED_TABLES
        for index in inspector.get_indexes(table_name)
    }
    assert EXPECTED_COMPOSITE_INDEXES <= index_names

    for table_name in EXPECTED_TABLES:
        check_names = {
            constraint["name"] for constraint in inspector.get_check_constraints(table_name)
        }
        assert f"ck_{table_name}_demo_marker" in check_names


def test_demo_marker_is_strict_and_is_only_data_provenance(database: Session) -> None:
    demo_without_key = User(
        email="missing-key@example.invalid",
        phone="1000000001",
        password_hash="hash",
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        is_demo=True,
        demo_key=None,
    )
    database.add(demo_without_key)
    with pytest.raises(IntegrityError):
        database.flush()
    database.rollback()

    production_with_demo_key = User(
        email="mislabeled@example.invalid",
        phone="1000000002",
        password_hash="hash",
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        is_demo=False,
        demo_key="must-not-label-production-data",
    )
    database.add(production_with_demo_key)
    with pytest.raises(IntegrityError):
        database.flush()
    database.rollback()

    demo = _user(
        database,
        suffix="9001demo",
        is_demo=True,
        demo_key="test:demo-user",
    )
    production = _user(database, suffix="9002real")
    assert demo.is_demo is True
    assert production.is_demo is False
    assert set(User.__table__.columns.keys()) >= {"is_demo", "demo_key", "status"}


def test_complete_relationship_graph_ownership_statuses_and_timestamps(
    database: Session,
) -> None:
    owner = _user(database, suffix="1001owner")
    assignee = _user(
        database,
        suffix="1002staff",
        role=Role.COUNSELLOR,
    )
    admin = _user(
        database,
        suffix="1003admin",
        role=Role.ADMIN,
    )

    profile = Profile(
        user_id=owner.id,
        full_name="Owner Demo",
        display_name="Owner",
        preferred_language="English",
        city_or_district="Demo District",
        consent_at=datetime.now(timezone.utc),
    )
    case = Case(
        owner_user_id=owner.id,
        case_number="DB-TEST-1001",
        category="synthetic",
        category_verified=False,
        stage="intake",
        court_name=None,
        summary="Synthetic database test case",
    )
    database.add_all([profile, case])
    database.flush()

    document = CaseDocument(
        case_id=case.id,
        owner_user_id=owner.id,
        filename="synthetic.pdf",
        mime_type="application/pdf",
        storage_path=None,
        uploaded_at=datetime.now(timezone.utc),
    )
    checkin = Checkin(
        user_id=owner.id,
        case_id=case.id,
        text="Synthetic database test check-in",
    )
    support_request = SupportRequest(
        user_id=owner.id,
        case_id=case.id,
        type=SupportRequestType.WELLBEING,
        status=SupportRequestStatus.ASSIGNED,
        priority="standard",
        explicit_human_request=True,
        details="Synthetic database test request",
    )
    database.add_all([document, checkin, support_request])
    database.flush()

    assignment = CaseAssignment(
        case_id=case.id,
        support_request_id=support_request.id,
        assignee_user_id=assignee.id,
        assigned_by_user_id=admin.id,
        assignment_type="wellbeing_counsellor",
        reason="Synthetic test assignment",
    )
    action = SupportAction(
        support_request_id=support_request.id,
        actor_user_id=assignee.id,
        action="follow_up_recorded",
        notes="Synthetic test action",
    )
    notification = Notification(
        user_id=owner.id,
        case_id=case.id,
        type="support_workflow",
        title="Synthetic assignment",
        message="Synthetic test notification",
    )
    conversation = AIConversation(
        user_id=owner.id,
        case_id=case.id,
        title="Synthetic test conversation",
    )
    database.add_all([assignment, action, notification, conversation])
    database.flush()

    message = AIMessage(
        conversation_id=conversation.id,
        role=AIMessageRole.USER,
        content="Synthetic test message",
    )
    audit = AuditLog(
        actor_user_id=admin.id,
        action="database_test",
        resource_type="case",
        resource_id=case.case_number,
        metadata_json={"synthetic": True},
    )
    database.add_all([message, audit])
    database.commit()

    assert owner.profile is profile
    assert owner.owned_cases == [case]
    assert owner.owned_case_documents == [document]
    assert owner.checkins == [checkin]
    assert owner.support_requests == [support_request]
    assert owner.notifications == [notification]
    assert owner.ai_conversations == [conversation]
    assert case.documents == [document]
    assert case.checkins == [checkin]
    assert case.support_requests == [support_request]
    assert case.assignments == [assignment]
    assert support_request.assignments == [assignment]
    assert support_request.actions == [action]
    assert assignee.assignments_received == [assignment]
    assert admin.assignments_created == [assignment]
    assert assignee.support_actions == [action]
    assert conversation.messages == [message]
    assert admin.audit_logs == [audit]

    assert case.status == CaseStatus.OPEN
    assert document.status == DocumentStatus.STORED
    assert checkin.analysis_status == CheckinAnalysisStatus.NOT_RUN
    assert assignment.status == AssignmentStatus.ACTIVE
    assert assignment.active is True
    assert action.status == SupportActionStatus.RECORDED
    assert notification.is_read is False
    assert conversation.status == AIConversationStatus.ACTIVE
    assert message.role == AIMessageRole.USER
    assert message.status == AIMessageStatus.COMPLETE

    for record in (
        owner,
        profile,
        case,
        document,
        checkin,
        support_request,
        assignment,
        action,
        notification,
        conversation,
        message,
        audit,
    ):
        assert record.created_at is not None
        assert record.updated_at is not None


def test_profile_cascade_and_case_ownership_restrict(database: Session) -> None:
    owner = _user(database, suffix="2001owner")
    database.add(
        Profile(
            user_id=owner.id,
            full_name="Owner Demo",
            display_name="Owner",
            preferred_language="English",
            city_or_district="Demo District",
            consent_at=datetime.now(timezone.utc),
        )
    )
    database.add(
        Case(
            owner_user_id=owner.id,
            case_number="DB-TEST-2001",
            category="synthetic",
            category_verified=False,
            stage="intake",
        )
    )
    database.commit()

    database.delete(owner)
    with pytest.raises(IntegrityError):
        database.flush()
    database.rollback()
