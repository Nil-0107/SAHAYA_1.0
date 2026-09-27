"""Controlled, idempotent seed for synthetic SAATHI demo personas.

Run from the ``backend`` directory with::

    SAATHI_ENV=development python -m app.demo.seed_demo

There is intentionally no HTTP route for this operation. The command refuses
production, staging, and production-looking database identifiers. Every row it
upserts is explicitly marked ``is_demo=True`` and receives a stable demo key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.config import (
    ALLOWED_DEMO_ENVIRONMENTS,
    DemoSeedEnvironmentError,
    Settings,
    get_settings,
)
from app.core.security import hash_password
from app.db.database import session_scope
from app.db.init_db import initialize_database
from app.demo.personas import DEMO_PERSONAS
from app.models import (
    AssignmentStatus,
    AssignmentType,
    AuditLog,
    AdministrativeUnit,
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


SEED_VERSION = 1


class DemoSeedConflictError(RuntimeError):
    """A real/non-demo record would collide with the controlled seed."""


@dataclass(frozen=True, slots=True)
class SeedResult:
    created: int
    updated: int
    unchanged: int
    demo_users: int

    @property
    def total_managed(self) -> int:
        return self.created + self.updated + self.unchanged


ManagedModel = TypeVar("ManagedModel", bound=Any)


def _demo_time(day: int, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc)


def _comparable_value(current: Any, incoming: Any) -> tuple[Any, Any]:
    """Normalise timezone-aware datetimes for SQLite's naive return values."""
    if isinstance(current, datetime) and isinstance(incoming, datetime):
        if current.tzinfo is None and incoming.tzinfo is not None:
            current = current.replace(tzinfo=timezone.utc)
        elif incoming.tzinfo is None and current.tzinfo is not None:
            incoming = incoming.replace(tzinfo=None)
    return current, incoming


def _upsert(
    database: Session,
    model: type[ManagedModel],
    demo_key: str,
    values: dict[str, Any],
    *,
    preserve_on_update: frozenset[str] = frozenset(),
) -> tuple[ManagedModel, str]:
    """Create or reconcile one demo row without depending on autoincrement IDs."""
    record = database.scalar(select(model).where(model.demo_key == demo_key))
    if record is not None and not record.is_demo:
        raise DemoSeedConflictError(
            f"Refusing to modify non-demo {model.__tablename__} row with key {demo_key!r}."
        )

    if record is None:
        record = model(is_demo=True, demo_key=demo_key, **values)
        database.add(record)
        database.flush()
        return record, "created"

    changed = False
    for field, value in values.items():
        if field in preserve_on_update:
            continue
        current_value, incoming_value = _comparable_value(getattr(record, field), value)
        if current_value != incoming_value:
            setattr(record, field, incoming_value)
            changed = True
    if changed:
        record.updated_at = datetime.now(timezone.utc)
        database.flush()
        return record, "updated"
    return record, "unchanged"


def _reject_real_conflicts(
    database: Session,
    model: type[ManagedModel],
    fields: dict[str, Any],
    identity: str,
) -> None:
    clauses = [getattr(model, field) == value for field, value in fields.items()]
    if not clauses:
        return
    query: Select = select(model.id).where(model.is_demo.is_(False), or_(*clauses))
    if database.scalar(query) is not None:
        formatted = ", ".join(f"{key}={value!r}" for key, value in fields.items())
        raise DemoSeedConflictError(
            f"Refusing to seed {identity}: a non-demo {model.__tablename__} row already uses {formatted}."
        )


def _user(
    database: Session,
    key: str,
    *,
    full_name: str,
    display_name: str,
    email: str,
    phone: str,
    password: str,
    role: Role,
    language: str,
    district: str,
    emergency_name: str | None = None,
    emergency_phone: str | None = None,
    safe_contact_method: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    created_by_user_id: int | None = None,
    appointed_by_user_id: int | None = None,
) -> tuple[User, str, str]:
    _reject_real_conflicts(database, User, {"email": email, "phone": phone}, full_name)
    verified_at = _demo_time(20, 8)
    user, user_result = _upsert(
        database,
        User,
        key,
        {
            "email": email,
            "phone": phone,
            "password_hash": hash_password(password),
            "role": role,
            "state_id": state_id,
            "district_id": district_id,
            "created_by_user_id": created_by_user_id,
            "created_role": role if role != Role.VICTIM else None,
            "appointed_by_user_id": appointed_by_user_id,
            "appointed_at": verified_at if appointed_by_user_id else None,
            "status": UserStatus.ACTIVE,
            "phone_verified_at": verified_at,
            "profile_completed": True,
            "is_active": True,
        },
        preserve_on_update=frozenset({"password_hash"}),
    )
    _, profile_result = _upsert(
        database,
        Profile,
        f"profile:{key}",
        {
            "user_id": user.id,
            "full_name": full_name,
            "display_name": display_name,
            "preferred_language": language,
            "city_or_district": district,
            "emergency_contact_name": emergency_name,
            "emergency_contact_phone": emergency_phone,
            "safe_contact_method": safe_contact_method,
            "consent_at": verified_at,
        },
    )
    return user, user_result, profile_result


def seed_demo(database: Session | None = None) -> SeedResult:
    """Create/update a complete synthetic persona graph in one transaction.

    Repeated runs reconcile the same stable demo keys. No real/non-demo row is
    ever selected for update, and a natural-key collision raises before write.
    """
    raw_environment = os.getenv("SAATHI_ENV", "").strip().lower()
    if raw_environment not in ALLOWED_DEMO_ENVIRONMENTS:
        raise DemoSeedEnvironmentError(
            "Demo seeding is blocked unless SAATHI_ENV is development, local, or test."
        )
    settings: Settings = get_settings()
    settings.require_demo_seed_allowed()
    settings.reject_obvious_production_database()

    owns_database = database is None
    if owns_database:
        initialize_database()

    counts = {"created": 0, "updated": 0, "unchanged": 0}

    def record(result: str) -> None:
        counts[result] += 1

    with session_scope(database) as active_database:
        units: dict[str, AdministrativeUnit] = {}
        unit_specs = (
            ("unit:national:demo", "Demo National Programme", "national", None),
            ("unit:state:demo", "Demo State", "state", None),
            ("unit:district:demo", "Demo District", "district", "unit:state:demo"),
        )
        for key, name, unit_type, parent_key in unit_specs:
            parent = units.get(parent_key) if parent_key else None
            unit, unit_result = _upsert(
                active_database,
                AdministrativeUnit,
                key,
                {
                    "name": name,
                    "unit_type": unit_type,
                    "parent_id": parent.id if parent else None,
                },
            )
            units[key] = unit
            record(unit_result)

        # Create the administrative graph from the top down so the persisted
        # creator/appointment relationships match the required hierarchy.
        persona_by_key = {persona.key: persona for persona in DEMO_PERSONAS}
        persona_order = (
            "user:admin:national-rohan-demo",
            "user:admin:state-asha-demo",
            "user:district:kabir-demo",
            "user:counsellor:leela-demo",
            "user:victim:aarohi-demo",
            "user:victim:meher-demo",
        )
        personas: dict[str, User] = {}
        state_unit = units["unit:state:demo"]
        district_unit = units["unit:district:demo"]
        for key in persona_order:
            persona = persona_by_key[key]
            creator = personas.get("user:admin:national-rohan-demo") if persona.role == Role.STATE_ADMIN else None
            creator = personas.get("user:admin:state-asha-demo") if persona.role == Role.DISTRICT_ADMIN else creator
            appointer = personas.get("user:district:kabir-demo") if persona.role == Role.COUNSELLOR else None
            user, user_result, profile_result = _user(
                active_database,
                persona.key,
                full_name=persona.full_name,
                display_name=persona.display_name,
                email=persona.email,
                phone=persona.phone,
                password=persona.password,
                role=persona.role,
                language=persona.language,
                district=persona.district,
                emergency_name=persona.emergency_name,
                emergency_phone=persona.emergency_phone,
                safe_contact_method=persona.safe_contact_method,
                state_id=state_unit.id if persona.role != Role.NATIONAL_ADMIN else None,
                district_id=district_unit.id if persona.role in {Role.VICTIM, Role.COUNSELLOR, Role.DISTRICT_ADMIN} else None,
                created_by_user_id=creator.id if creator else None,
                appointed_by_user_id=appointer.id if appointer else None,
            )
            personas[key] = user
            record(user_result)
            record(profile_result)

        aarohi = personas["user:victim:aarohi-demo"]
        meher = personas["user:victim:meher-demo"]
        counsellor = personas["user:counsellor:leela-demo"]
        district_officer = personas["user:district:kabir-demo"]
        state_admin = personas["user:admin:state-asha-demo"]
        national_admin = personas["user:admin:national-rohan-demo"]

        _reject_real_conflicts(
            active_database,
            Case,
            {"case_number": "SA-DEMO-1001"},
            "Aarohi demo case",
        )
        aarohi_case, result = _upsert(
            active_database,
            Case,
            "case:aarohi:1001",
            {
                "owner_user_id": aarohi.id,
                "case_number": "SA-DEMO-1001",
                "category": "synthetic_legal_assistance",
                "category_verified": False,
                "status": CaseStatus.OPEN,
                "stage": "investigation_demo",
                "court_name": "Fictional Demo District Court",
                "next_hearing": _demo_time(30, 10),
                "summary": "Synthetic demonstration case. No real person, court, incident, or legal status is represented.",
                "protection_request_open": True,
                "wellbeing_review_verified": False,
            },
        )
        record(result)

        _reject_real_conflicts(
            active_database,
            Case,
            {"case_number": "SA-DEMO-1002"},
            "Meher demo case",
        )
        meher_case, result = _upsert(
            active_database,
            Case,
            "case:meher:1002",
            {
                "owner_user_id": meher.id,
                "case_number": "SA-DEMO-1002",
                "category": "synthetic_wellbeing_support",
                "category_verified": False,
                "status": CaseStatus.OPEN,
                "stage": "support_demo",
                "court_name": None,
                "next_hearing": None,
                "summary": "Synthetic well-being support scenario with no real case or legal claim.",
                "protection_request_open": False,
                "wellbeing_review_verified": True,
            },
        )
        record(result)

        _reject_real_conflicts(
            active_database,
            Case,
            {"case_number": "SA-DEMO-1003"},
            "High-priority synthetic demo case",
        )
        _, result = _upsert(
            active_database,
            Case,
            "case:meher:1003",
            {
                "owner_user_id": meher.id,
                "case_number": "SA-DEMO-1003",
                "category": "witness_intimidation_or_threats",
                "category_verified": True,
                "status": CaseStatus.OPEN,
                "stage": "authorised_review_demo",
                "court_name": None,
                "next_hearing": None,
                "summary": "Synthetic high-priority routing fixture. No real incident, threat, person, or legal status is represented.",
                "protection_request_open": False,
                "wellbeing_review_verified": False,
            },
        )
        record(result)

        _reject_real_conflicts(
            active_database,
            Case,
            {"case_number": "SA-DEMO-1004"},
            "Standard-priority synthetic demo case",
        )
        _, result = _upsert(
            active_database,
            Case,
            "case:aarohi:1004",
            {
                "owner_user_id": aarohi.id,
                "case_number": "SA-DEMO-1004",
                "category": "synthetic_standard_support",
                "category_verified": False,
                "status": CaseStatus.OPEN,
                "stage": "standard_review_demo",
                "court_name": None,
                "next_hearing": None,
                "summary": "Synthetic standard-routing fixture with no qualifying priority factors recorded.",
                "protection_request_open": False,
                "wellbeing_review_verified": False,
            },
        )
        record(result)

        # Document metadata is realistic, but points to no file and no real case.
        _, result = _upsert(
            active_database,
            CaseDocument,
            "document:aarohi:1001:hearing-notice-demo",
            {
                "case_id": aarohi_case.id,
                "owner_user_id": aarohi.id,
                "filename": "SYNTHETIC_demo_hearing_notice.pdf",
                "mime_type": "application/pdf",
                "storage_path": None,
                "status": DocumentStatus.STORED,
                "extracted_json": {
                    "synthetic": True,
                    "document_kind": "illustrative_hearing_notice",
                    "notice": "Not a real legal notice or official record.",
                },
                "uploaded_at": _demo_time(21, 11),
            },
        )
        record(result)
        _, result = _upsert(
            active_database,
            CaseDocument,
            "document:aarohi:1001:case-summary-demo",
            {
                "case_id": aarohi_case.id,
                "owner_user_id": aarohi.id,
                "filename": "SYNTHETIC_demo_case_summary.png",
                "mime_type": "image/png",
                "storage_path": None,
                "status": DocumentStatus.STORED,
                "extracted_json": {
                    "synthetic": True,
                    "document_kind": "illustrative_case_summary",
                },
                "uploaded_at": _demo_time(22, 12),
            },
        )
        record(result)
        _, result = _upsert(
            active_database,
            CaseDocument,
            "document:meher:1002:support-note-demo",
            {
                "case_id": meher_case.id,
                "owner_user_id": meher.id,
                "filename": "SYNTHETIC_demo_support_note.pdf",
                "mime_type": "application/pdf",
                "storage_path": None,
                "status": DocumentStatus.STORED,
                "extracted_json": {
                    "synthetic": True,
                    "document_kind": "illustrative_support_note",
                },
                "uploaded_at": _demo_time(21, 13),
            },
        )
        record(result)

        # No ML class or confidence is fabricated. These seed responses are
        # visible only to demonstrate workflow relationships.
        checkin_values = (
            (
                "checkin:aarohi:2026-09-21",
                aarohi,
                aarohi_case,
                "Synthetic demo response: the upcoming case milestone is making me worried and sleep has been difficult.",
                _demo_time(21, 18),
            ),
            (
                "checkin:aarohi:2026-09-23",
                aarohi,
                aarohi_case,
                "Synthetic demo response: I spoke with my support person and feel somewhat steadier today, but uncertainty remains.",
                _demo_time(23, 19),
            ),
            (
                "checkin:aarohi:2026-09-24",
                aarohi,
                aarohi_case,
                "Synthetic demo response: I would like human support and clearer information about the next process step.",
                _demo_time(24, 20),
            ),
            (
                "checkin:meher:2026-09-24",
                meher,
                meher_case,
                "Synthetic demo response: talking to someone has helped; I would like one planned follow-up.",
                _demo_time(24, 17),
            ),
        )
        for key, owner, case, text, created_at in checkin_values:
            _, result = _upsert(
                active_database,
                Checkin,
                key,
                {
                    "user_id": owner.id,
                    "case_id": case.id,
                    "text": text,
                    "analysis_status": CheckinAnalysisStatus.NOT_RUN,
                    "predicted_class": None,
                    "predicted_label": None,
                    "confidence": None,
                    "created_at": created_at,
                },
            )
            record(result)

        support_specs = (
            (
                "support:aarohi:wellbeing:1",
                aarohi,
                aarohi_case,
                SupportRequestType.WELLBEING,
                SupportRequestStatus.ASSIGNED,
                "normal",
                "Synthetic demo request: please arrange a counsellor follow-up about case-related worry and sleep.",
                None,
            ),
            (
                "support:aarohi:legal:1",
                aarohi,
                aarohi_case,
                SupportRequestType.LEGAL,
                SupportRequestStatus.ASSIGNED,
                "normal",
                "Synthetic demo request: request authorised human legal-assistance coordination for the illustrative case.",
                None,
            ),
            (
                "support:aarohi:protection:1",
                aarohi,
                aarohi_case,
                SupportRequestType.PROTECTION,
                SupportRequestStatus.IN_PROGRESS,
                "high",
                "Synthetic demo request: open a protection review workflow. This seed does not contact any emergency service.",
                None,
            ),
            (
                "support:meher:wellbeing:1",
                meher,
                meher_case,
                SupportRequestType.WELLBEING,
                SupportRequestStatus.ASSIGNED,
                "normal",
                "Synthetic demo request: schedule one authorised counsellor follow-up.",
                None,
            ),
            (
                "support:meher:legal:1",
                meher,
                meher_case,
                SupportRequestType.LEGAL,
                SupportRequestStatus.ASSIGNED,
                "normal",
                "Synthetic demo request: authorise a district review of an illustrative legal-support need.",
                None,
            ),
        )
        support_requests: dict[str, SupportRequest] = {}
        for key, owner, case, request_type, status, priority, details, resolved_at in support_specs:
            request, result = _upsert(
                active_database,
                SupportRequest,
                key,
                {
                    "user_id": owner.id,
                    "case_id": case.id,
                    "type": request_type,
                    "status": status,
                    "priority": priority,
                    "explicit_human_request": True,
                    "details": details,
                    "resolved_at": resolved_at,
                },
            )
            support_requests[key] = request
            record(result)

        assignment_specs = (
            (
                "assignment:aarohi:wellbeing:counsellor",
                aarohi_case,
                support_requests["support:aarohi:wellbeing:1"],
                counsellor,
                state_admin,
                AssignmentType.WELLBEING_COUNSELLOR,
                "Synthetic demo assignment: authorised well-being follow-up only.",
            ),
            (
                "assignment:aarohi:legal:district",
                aarohi_case,
                support_requests["support:aarohi:legal:1"],
                district_officer,
                state_admin,
                AssignmentType.DISTRICT_COORDINATION,
                "Synthetic demo assignment: district-level review of the legal-assistance request.",
            ),
            (
                "assignment:aarohi:protection:district",
                aarohi_case,
                support_requests["support:aarohi:protection:1"],
                district_officer,
                state_admin,
                AssignmentType.DISTRICT_COORDINATION,
                "Synthetic demo assignment: review the open protection workflow within district scope.",
            ),
            (
                "assignment:meher:wellbeing:counsellor",
                meher_case,
                support_requests["support:meher:wellbeing:1"],
                counsellor,
                state_admin,
                AssignmentType.WELLBEING_COUNSELLOR,
                "Synthetic demo assignment: authorised planned follow-up only.",
            ),
            (
                "assignment:meher:legal:district",
                meher_case,
                support_requests["support:meher:legal:1"],
                district_officer,
                state_admin,
                AssignmentType.DISTRICT_COORDINATION,
                "Synthetic demo assignment: district review of an illustrative legal-support request.",
            ),
        )
        for key, case, request, assignee, assigned_by, assignment_type, reason in assignment_specs:
            _, result = _upsert(
                active_database,
                CaseAssignment,
                key,
                {
                    "case_id": case.id,
                    "support_request_id": request.id,
                    "assignee_user_id": assignee.id,
                    "assigned_by_user_id": assigned_by.id,
                    "assignment_type": assignment_type,
                    "status": AssignmentStatus.ACTIVE,
                    "reason": reason,
                    "active": True,
                    "assigned_at": _demo_time(24, 7),
                },
            )
            record(result)

        action_specs = (
            (
                "action:aarohi:wellbeing:acknowledged",
                support_requests["support:aarohi:wellbeing:1"],
                counsellor,
                "Synthetic demo counsellor acknowledgement recorded",
                "Synthetic demo note: initial contact preference agreed; no clinical assessment or diagnosis is represented.",
                _demo_time(24, 8),
            ),
            (
                "action:aarohi:legal:reviewed",
                support_requests["support:aarohi:legal:1"],
                district_officer,
                "Synthetic demo district review recorded",
                "Synthetic demo note: illustrative legal-assistance context queued for authorised follow-up; no legal conclusion made.",
                _demo_time(24, 9),
            ),
            (
                "action:aarohi:protection:review-opened",
                support_requests["support:aarohi:protection:1"],
                district_officer,
                "Synthetic demo protection review opened",
                "Synthetic demo note: internal review workflow opened; no police, emergency, or outside service was contacted.",
                _demo_time(24, 10),
            ),
            (
                "action:aarohi:wellbeing:follow-up",
                support_requests["support:aarohi:wellbeing:1"],
                counsellor,
                "Synthetic demo counsellor follow-up completed",
                "Synthetic demo note: supportive follow-up was recorded; no diagnosis, risk score, or external contact is represented.",
                _demo_time(25, 8),
            ),
            (
                "action:aarohi:legal:coordination",
                support_requests["support:aarohi:legal:1"],
                district_officer,
                "Synthetic demo district coordination recorded",
                "Synthetic demo note: internal coordination notes were recorded; no lawyer, court, police, or outside service was contacted.",
                _demo_time(25, 9),
            ),
            (
                "action:meher:legal:reviewed",
                support_requests["support:meher:legal:1"],
                district_officer,
                "Synthetic demo district legal-support review recorded",
                "Synthetic demo note: an authorised district review was recorded; no legal conclusion or outside contact is represented.",
                _demo_time(25, 10),
            ),
            (
                "action:meher:wellbeing:scheduled",
                support_requests["support:meher:wellbeing:1"],
                counsellor,
                "Synthetic demo follow-up prepared",
                "Synthetic demo note: planned follow-up workflow prepared; scheduling details are fictional.",
                _demo_time(24, 11),
            ),
        )
        for key, request, actor, action, notes, created_at in action_specs:
            _, result = _upsert(
                active_database,
                SupportAction,
                key,
                {
                    "support_request_id": request.id,
                    "actor_user_id": actor.id,
                    "action": action,
                    "status": SupportActionStatus.RECORDED,
                    "notes": notes,
                    "created_at": created_at,
                },
            )
            record(result)

        notification_specs = (
            (
                "notification:aarohi:counsellor-assigned",
                aarohi,
                aarohi_case,
                "Counsellor follow-up assigned",
                "Synthetic demo notification: your well-being support request is assigned to Dr Leela Demo.",
                False,
                None,
            ),
            (
                "notification:aarohi:case-update",
                aarohi,
                aarohi_case,
                "Synthetic case update",
                "Synthetic demo case update: an illustrative timeline entry is available. No court response or government verification is represented.",
                False,
                None,
            ),
            (
                "notification:aarohi:checkin-reminder",
                aarohi,
                aarohi_case,
                "Check-in history available",
                "Synthetic demo notification: your saved check-in history is available in My Case and Well-being check-in.",
                False,
                None,
            ),
            (
                "notification:meher:counsellor-assigned",
                meher,
                meher_case,
                "Counsellor follow-up assigned",
                "Synthetic demo notification: your support request is assigned to Dr Leela Demo.",
                False,
                None,
            ),
            (
                "notification:meher:district-assigned",
                meher,
                meher_case,
                "District legal-support review assigned",
                "Synthetic demo notification: your illustrative legal-support request is assigned to Kabir Demo.",
                False,
                None,
            ),
            (
                "notification:counsellor:aarohi-new",
                counsellor,
                aarohi_case,
                "New synthetic well-being request",
                "Synthetic demo queue item: one well-being request is assigned for authorised follow-up.",
                False,
                None,
            ),
            (
                "notification:counsellor:meher-followup",
                counsellor,
                meher_case,
                "Synthetic follow-up prepared",
                "Synthetic demo queue item: one planned well-being follow-up is ready.",
                True,
                _demo_time(24, 12),
            ),
            (
                "notification:district:legal-review",
                district_officer,
                aarohi_case,
                "Legal-assistance request assigned",
                "Synthetic demo queue item: district review is required for the illustrative legal-assistance request.",
                False,
                None,
            ),
            (
                "notification:district:protection-review",
                district_officer,
                aarohi_case,
                "Protection review in progress",
                "Synthetic demo queue item: an internal protection review workflow is open.",
                False,
                None,
            ),
            (
                "notification:district:meher-legal-review",
                district_officer,
                meher_case,
                "Second synthetic legal-support review",
                "Synthetic demo queue item: a second authorised district case is available for illustrative review.",
                False,
                None,
            ),
            (
                "notification:state:coordination-summary",
                state_admin,
                aarohi_case,
                "Synthetic coordination summary",
                "Synthetic demo summary: assigned counsellor and district workflows are available within authorised scope.",
                True,
                _demo_time(24, 13),
            ),
            (
                "notification:national:programme-summary",
                national_admin,
                aarohi_case,
                "Synthetic programme summary",
                "Synthetic demo aggregate marker: demo cases and assignments are available to aggregate reporting.",
                True,
                _demo_time(24, 14),
            ),
        )
        for key, recipient, case, title, message, is_read, read_at in notification_specs:
            _, result = _upsert(
                active_database,
                Notification,
                key,
                {
                    "user_id": recipient.id,
                    "case_id": case.id,
                    "type": "support_workflow",
                    "title": title,
                    "message": message,
                    "is_read": is_read,
                    "read_at": read_at,
                },
            )
            record(result)

        audit_specs = (
            (
                "audit:hierarchy:national-created-state",
                national_admin,
                "DEMO_STATE_ADMIN_CREATED",
                "user",
                str(state_admin.id),
                {"synthetic": True, "created_role": Role.STATE_ADMIN.value, "created_by_role": Role.NATIONAL_ADMIN.value},
                _demo_time(19, 8),
            ),
            (
                "audit:hierarchy:state-created-district",
                state_admin,
                "DEMO_DISTRICT_ADMIN_CREATED",
                "user",
                str(district_officer.id),
                {"synthetic": True, "created_role": Role.DISTRICT_ADMIN.value, "created_by_role": Role.STATE_ADMIN.value},
                _demo_time(19, 9),
            ),
            (
                "audit:hierarchy:district-appointed-counsellor",
                district_officer,
                "DEMO_COUNSELLOR_APPOINTED",
                "user",
                str(counsellor.id),
                {"synthetic": True, "created_role": Role.COUNSELLOR.value, "appointed_by_role": Role.DISTRICT_ADMIN.value},
                _demo_time(19, 10),
            ),
            (
                "audit:aarohi:counsellor-assigned",
                state_admin,
                "DEMO_CASE_ASSIGNED",
                "case_assignment",
                "aarohi-wellbeing",
                {"request_type": "wellbeing", "synthetic": True, "seed_version": SEED_VERSION},
                _demo_time(24, 7, 30),
            ),
            (
                "audit:aarohi:district-review",
                state_admin,
                "DEMO_CASE_ASSIGNED",
                "case_assignment",
                "aarohi-district",
                {"request_type": "legal_and_protection", "synthetic": True, "seed_version": SEED_VERSION},
                _demo_time(24, 7, 45),
            ),
            (
                "audit:counsellor:action",
                counsellor,
                "DEMO_SUPPORT_ACTION_RECORDED",
                "support_request",
                "aarohi-wellbeing",
                {"synthetic": True, "diagnosis_represented": False, "seed_version": SEED_VERSION},
                _demo_time(24, 8, 10),
            ),
            (
                "audit:district:protection",
                district_officer,
                "DEMO_PROTECTION_WORKFLOW_OPENED",
                "support_request",
                "aarohi-protection",
                {"synthetic": True, "external_contact_claimed": False, "seed_version": SEED_VERSION},
                _demo_time(24, 10, 5),
            ),
            (
                "audit:aarohi:case-timeline",
                state_admin,
                "DEMO_CASE_TIMELINE",
                "case",
                aarohi_case.case_number,
                {
                    "synthetic": True,
                    "events": [
                        {"date": "2026-09-20", "label": "Illustrative case opened"},
                        {"date": "2026-09-21", "label": "Synthetic document metadata added"},
                        {"date": "2026-09-24", "label": "Human support requests created"},
                        {"date": "2026-09-30", "label": "Fictional next-hearing milestone"},
                    ],
                    "seed_version": SEED_VERSION,
                },
                _demo_time(24, 10, 30),
            ),
            (
                "audit:admin:priority-standard-example",
                state_admin,
                "DEMO_PRIORITY_EXAMPLE",
                "support_request",
                "aarohi-wellbeing",
                {
                    "synthetic": True,
                    "display_category": "STANDARD",
                    "reason": "Explicit human support request without a verified high-priority category",
                    "seed_version": SEED_VERSION,
                },
                _demo_time(24, 11),
            ),
            (
                "audit:admin:priority-elevated-example",
                national_admin,
                "DEMO_PRIORITY_EXAMPLE",
                "support_request",
                "aarohi-protection",
                {
                    "synthetic": True,
                    "display_category": "ELEVATED",
                    "reason": "Open protection request plus explicit human support",
                    "seed_version": SEED_VERSION,
                },
                _demo_time(24, 11, 30),
            ),
            (
                "audit:admin:aggregate-snapshot",
                national_admin,
                "DEMO_ADMIN_AGGREGATE_SNAPSHOT",
                "programme_dashboard",
                "national-demo-snapshot",
                {
                    "synthetic": True,
                    "active_demo_cases": 4,
                    "demo_support_requests": 5,
                    "demo_open_assignments": 5,
                    "demo_checkins": 4,
                    "priority_examples": {"STANDARD": 4, "ELEVATED": 1},
                    "contains_sensitive_victim_content": False,
                    "seed_version": SEED_VERSION,
                },
                _demo_time(24, 12),
            ),
        )
        for key, actor, action, resource_type, resource_id, metadata_json, created_at in audit_specs:
            _, result = _upsert(
                active_database,
                AuditLog,
                key,
                {
                    "actor_user_id": actor.id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "metadata_json": metadata_json,
                    "created_at": created_at,
                },
            )
            record(result)

        demo_users = active_database.scalar(
            select(User.id).where(User.is_demo.is_(True)).limit(1)
        )
        if demo_users is None:
            raise RuntimeError("Demo seed completed without a marked demo user")

    return SeedResult(
        created=counts["created"],
        updated=counts["updated"],
        unchanged=counts["unchanged"],
        demo_users=6,
    )


def main() -> None:
    try:
        result = seed_demo()
    except Exception as exc:
        raise SystemExit(f"Demo seed refused: {exc}") from exc

    print("SAATHI synthetic demo personas are ready.")
    print(f"Created: {result.created}; updated: {result.updated}; unchanged: {result.unchanged}")
    print(f"Demo users: {result.demo_users}")
    print("Unique development credentials are documented in docs/DEMO_ACCOUNTS.md.")
    print("All seeded records are marked is_demo=true. No public seed API exists.")


if __name__ == "__main__":
    main()
