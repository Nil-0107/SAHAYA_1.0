"""Administrator-only aggregate dashboard API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models.user import Role, User
from app.schemas.administration import (
    AccountStatusUpdate,
    AdministrativeAccountCreate,
    AdministrativeAccountResponse,
    AdministrativeUnitResponse,
)
from app.schemas.admin import (
    AdminAggregate,
    AdminAuditEntry,
    AdminDashboardResponse,
    AdminDistrictAnalytics,
    AdminEscalationTrendPoint,
    AdminPriorityQueueItem,
    AdminSupportCountBucket,
    AdminSupportRequestCounts,
    AdminUserDetail,
)
from app.schemas.notification import NotificationResponse
from app.services.admin_service import AdminDashboardService
from app.services.administration_service import AdministrationError, AdministrationService


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def admin_dashboard(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    include_demo: bool = Query(False),
) -> AdminDashboardResponse:
    data = AdminDashboardService(database).dashboard(user=user, include_demo=include_demo)
    support_counts = data["support_request_counts"]
    return AdminDashboardResponse(
        aggregate=AdminAggregate(**data["aggregate"]),
        district_analytics=[AdminDistrictAnalytics(**item) for item in data["district_analytics"]],
        support_request_counts=AdminSupportRequestCounts(
            by_type=[AdminSupportCountBucket(**item) for item in support_counts["by_type"]],
            by_status=[AdminSupportCountBucket(**item) for item in support_counts["by_status"]],
        ),
        priority_queue=[AdminPriorityQueueItem(**item) for item in data["priority_queue"]],
        escalation_trends=[AdminEscalationTrendPoint(**item) for item in data["escalation_trends"]],
        notifications=[NotificationResponse.model_validate(item) for item in data["notifications"]],
        audit_entries=[AdminAuditEntry(**item) for item in data["audit_entries"]],
    )


@router.get("/audit", response_model=list[AdminAuditEntry])
def admin_audit_log(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    include_demo: bool = Query(False),
) -> list[AdminAuditEntry]:
    data = AdminDashboardService(database).dashboard(user=user, include_demo=include_demo)
    return [AdminAuditEntry(**item) for item in data["audit_entries"]]


@router.get("/queue", response_model=list[AdminPriorityQueueItem])
def admin_priority_queue(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    include_demo: bool = Query(False),
) -> list[AdminPriorityQueueItem]:
    data = AdminDashboardService(database).dashboard(user=user, include_demo=include_demo)
    return [AdminPriorityQueueItem(**item) for item in data["priority_queue"]]


def _case_priority(
    *,
    case_id: int,
    user: User,
    database: Session,
) -> AdminPriorityQueueItem:
    data = AdminDashboardService(database).dashboard(user=user)
    for item in data["priority_queue"]:
        if item["case_id"] == case_id:
            return AdminPriorityQueueItem(**item)
    raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Case not found"})


@router.get("/cases/{case_id}", response_model=AdminPriorityQueueItem)
def admin_case_priority(
    case_id: int = Path(gt=0),
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> AdminPriorityQueueItem:
    return _case_priority(case_id=case_id, user=user, database=database)


@router.post("/cases/{case_id}/priority-recalculate", response_model=AdminPriorityQueueItem)
def admin_recalculate_case_priority(
    case_id: int = Path(gt=0),
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    include_demo: bool = Query(False),
) -> AdminPriorityQueueItem:
    data = AdminDashboardService(database).dashboard(user=user, include_demo=include_demo)
    for item in data["priority_queue"]:
        if item["case_id"] == case_id:
            return AdminPriorityQueueItem(**item)
    raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Case not found"})


def _raise_administration_error(database: Session, error: AdministrationError) -> None:
    database.rollback()
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


def _account_response(user: User) -> AdministrativeAccountResponse:
    profile = user.profile
    return AdministrativeAccountResponse(
        id=user.id,
        full_name=profile.full_name if profile else user.email or "Administrative account",
        display_name=profile.display_name if profile else user.email or "Account",
        email=user.email,
        phone=user.phone,
        role=user.role,
        status=user.status,
        state_id=user.state_id,
        district_id=user.district_id,
        state_name=user.state_unit.name if user.state_unit else None,
        district_name=user.district_unit.name if user.district_unit else None,
        created_by_user_id=user.created_by_user_id,
        created_role=user.created_role,
        appointed_by_user_id=user.appointed_by_user_id,
        appointed_at=user.appointed_at,
        created_at=user.created_at,
        is_demo=user.is_demo,
    )


@router.get("/users", response_model=list[AdminUserDetail])
def admin_users(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
    include_demo: bool = Query(False),
) -> list[AdminUserDetail]:
    return [AdminUserDetail(**item) for item in AdminDashboardService(database).user_directory(user=user, include_demo=include_demo)]


@router.post("/state-administrators", response_model=AdministrativeAccountResponse, status_code=201)
def create_state_administrator(
    payload: AdministrativeAccountCreate,
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN)),
    database: Session = Depends(get_db),
) -> AdministrativeAccountResponse:
    try:
        created = AdministrationService(database).create_state_admin(actor=user, payload=payload)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return _account_response(created)


@router.get("/state-administrators", response_model=list[AdministrativeAccountResponse])
def list_state_administrators(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN)),
    database: Session = Depends(get_db),
) -> list[AdministrativeAccountResponse]:
    try:
        accounts = AdministrationService(database).list_accounts(actor=user, role=Role.STATE_ADMIN)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return [_account_response(account) for account in accounts]


@router.post("/district-administrators", response_model=AdministrativeAccountResponse, status_code=201)
def create_district_administrator(
    payload: AdministrativeAccountCreate,
    user: User = Depends(require_roles(Role.STATE_ADMIN)),
    database: Session = Depends(get_db),
) -> AdministrativeAccountResponse:
    try:
        created = AdministrationService(database).create_district_admin(actor=user, payload=payload)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return _account_response(created)


@router.get("/district-administrators", response_model=list[AdministrativeAccountResponse])
def list_district_administrators(
    user: User = Depends(require_roles(Role.STATE_ADMIN)),
    database: Session = Depends(get_db),
) -> list[AdministrativeAccountResponse]:
    try:
        accounts = AdministrationService(database).list_accounts(actor=user, role=Role.DISTRICT_ADMIN)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return [_account_response(account) for account in accounts]


@router.post("/counsellors", response_model=AdministrativeAccountResponse, status_code=201)
def appoint_counsellor(
    payload: AdministrativeAccountCreate,
    user: User = Depends(require_roles(Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> AdministrativeAccountResponse:
    try:
        created = AdministrationService(database).create_counsellor(actor=user, payload=payload)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return _account_response(created)


@router.get("/counsellors", response_model=list[AdministrativeAccountResponse])
def list_counsellors(
    user: User = Depends(require_roles(Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> list[AdministrativeAccountResponse]:
    try:
        accounts = AdministrationService(database).list_accounts(actor=user, role=Role.COUNSELLOR)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return [_account_response(account) for account in accounts]


@router.patch("/accounts/{user_id}/status", response_model=AdministrativeAccountResponse)
def update_administrative_account_status(
    user_id: int = Path(gt=0),
    payload: AccountStatusUpdate | None = None,
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> AdministrativeAccountResponse:
    if payload is None:
        raise HTTPException(status_code=422, detail={"code": "STATUS_REQUIRED", "message": "Status is required"})
    try:
        account = AdministrationService(database).update_status(actor=user, target_user_id=user_id, payload=payload)
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return _account_response(account)


@router.get("/states", response_model=list[AdministrativeUnitResponse])
def list_states(
    user: User = Depends(require_roles(Role.NATIONAL_ADMIN, Role.STATE_ADMIN)),
    database: Session = Depends(get_db),
) -> list[AdministrativeUnitResponse]:
    try:
        units = AdministrationService(database).list_units(actor=user, unit_type="state")
    except AdministrationError as error:
        _raise_administration_error(database, error)
    if user.role == Role.STATE_ADMIN:
        units = [unit for unit in units if unit.id == user.state_id]
    return [AdministrativeUnitResponse.model_validate(unit) for unit in units]


@router.get("/districts", response_model=list[AdministrativeUnitResponse])
def list_districts(
    user: User = Depends(require_roles(Role.STATE_ADMIN, Role.DISTRICT_ADMIN)),
    database: Session = Depends(get_db),
) -> list[AdministrativeUnitResponse]:
    try:
        units = AdministrationService(database).list_units(actor=user, unit_type="district")
    except AdministrationError as error:
        _raise_administration_error(database, error)
    return [AdministrativeUnitResponse.model_validate(unit) for unit in units]
