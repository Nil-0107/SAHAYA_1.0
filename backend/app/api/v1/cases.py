"""Authenticated case and document API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_ready_user
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_document import CaseDocument
from app.models.support_request import SupportRequest
from app.models.user import User
from app.schemas.case import CaseCreate, CaseDocumentResponse, CaseResponse, CaseSupportSummary, CaseTimelineEvent
from app.services.case_service import CaseService, CaseServiceError


router = APIRouter(prefix="/cases", tags=["cases"])


def _raise_service_error(error: CaseServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


def _document_response(document: CaseDocument) -> CaseDocumentResponse:
    size = None
    if isinstance(document.extracted_json, dict):
        raw_size = document.extracted_json.get("size_bytes")
        if isinstance(raw_size, int):
            size = raw_size
    return CaseDocumentResponse(
        id=document.id,
        filename=document.filename,
        mime_type=document.mime_type,
        status=document.status,
        uploaded_at=document.uploaded_at,
        size_bytes=size,
        is_demo=document.is_demo,
    )


def _timeline(case: Case, database: Session, *, include_demo: bool) -> list[CaseTimelineEvent]:
    if not include_demo:
        return []
    rows = database.scalars(
        select(AuditLog)
        .where(
            AuditLog.resource_type == "case",
            AuditLog.resource_id == case.case_number,
            AuditLog.action == "DEMO_CASE_TIMELINE",
        )
        .order_by(AuditLog.created_at.asc())
    )
    events: list[CaseTimelineEvent] = []
    for row in rows:
        metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
        raw_events = metadata.get("events", [])
        if not isinstance(raw_events, list):
            continue
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            date = event.get("date")
            label = event.get("label")
            if isinstance(date, str) and isinstance(label, str):
                events.append(CaseTimelineEvent(date=date, label=label, is_demo=True))
    return events


def _case_response(case: Case, database: Session, *, include_demo: bool) -> CaseResponse:
    document_query = select(CaseDocument).where(CaseDocument.case_id == case.id)
    support_query = select(SupportRequest).where(SupportRequest.case_id == case.id)
    if not include_demo:
        document_query = document_query.where(CaseDocument.is_demo.is_(False))
        support_query = support_query.where(SupportRequest.is_demo.is_(False))
    documents = list(
        database.scalars(
            document_query
            .order_by(CaseDocument.uploaded_at.desc(), CaseDocument.id.desc())
        )
    )
    support_requests = list(
        database.scalars(
            support_query
            .order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())
        )
    )
    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        category=case.category,
        category_verified=case.category_verified,
        status=case.status,
        stage=case.stage,
        court_name=case.court_name,
        next_hearing=case.next_hearing,
        summary=case.summary,
        protection_request_open=case.protection_request_open,
        created_at=case.created_at,
        is_demo=case.is_demo,
        documents=[_document_response(document) for document in documents],
        support_information=[
            CaseSupportSummary(
                id=request.id,
                type=request.type.value,
                status=request.status.value,
                priority=request.priority,
                is_demo=request.is_demo,
            )
            for request in support_requests
        ],
        updates=[],
        timeline=_timeline(case, database, include_demo=include_demo),
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseResponse:
    if user.role.value != "victim":
        _raise_service_error(CaseServiceError(403, "CASE_CREATE_FORBIDDEN", "Only Victim / User accounts can create a case"))
    try:
        case = CaseService(database, settings).create_for_user(
            user=user,
            category=payload.category,
            summary=payload.summary,
        )
    except CaseServiceError as error:
        _raise_service_error(error)
    return _case_response(case, database, include_demo=settings.demo_data_enabled)


@router.post("/upload", response_model=CaseDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_case_document(
    case_id: int | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseDocumentResponse:
    try:
        document = await CaseService(database, settings).upload_document(
            user=user,
            case_id=case_id,
            upload=file,
        )
    except CaseServiceError as error:
        _raise_service_error(error)
    return _document_response(document)


@router.get("/me", response_model=list[CaseResponse])
def list_my_cases(
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[CaseResponse]:
    try:
        cases = CaseService(database, settings).list_for_user(user=user)
    except CaseServiceError as error:
        _raise_service_error(error)
    return [_case_response(case, database, include_demo=settings.demo_data_enabled) for case in cases]


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: int = Path(gt=0),
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseResponse:
    try:
        case = CaseService(database, settings).get_for_user(user=user, case_id=case_id)
    except CaseServiceError as error:
        _raise_service_error(error)
    return _case_response(case, database, include_demo=settings.demo_data_enabled)
