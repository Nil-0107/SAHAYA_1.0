"""Case ownership, metadata, and secure document-upload tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import get_db
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import seed_demo
from app.main import app
from app.models.audit_log import AuditLog
from app.models.case import Case, CaseStatus
from app.models.case_document import CaseDocument, DocumentStatus
from app.models.support_request import SupportRequest
from app.models.user import Role, User, UserStatus


PASSWORD = "ValidPass!123"


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Session, None, None]:
    monkeypatch.setenv("SAHAYA_ENV", "test")
    monkeypatch.setenv("SAHAYA_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SAHAYA_UPLOAD_DIRECTORY", str(tmp_path / "uploads"))
    monkeypatch.setenv("SAHAYA_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    active_session = sessionmaker(bind=engine, expire_on_commit=False)()

    def override_database() -> Generator[Session, None, None]:
        yield active_session

    app.dependency_overrides[get_db] = override_database
    yield active_session
    app.dependency_overrides.clear()
    active_session.close()
    engine.dispose()


@pytest.fixture
def client(database: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def _user(database: Session, suffix: str) -> User:
    user = User(
        phone=f"+9191000{suffix}",
        email=f"{suffix}@example.invalid",
        password_hash=hash_password(PASSWORD),
        role=Role.VICTIM,
        status=UserStatus.ACTIVE,
        phone_verified_at=datetime.now(timezone.utc),
        profile_completed=True,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def _case(database: Session, owner: User, number: str = "SA-TEST-1001") -> Case:
    case = Case(
        owner_user_id=owner.id,
        case_number=number,
        category="synthetic_case",
        category_verified=False,
        status=CaseStatus.OPEN,
        stage="investigation",
        summary="Synthetic test case. No real case or government verification is represented.",
    )
    database.add(case)
    database.commit()
    database.refresh(case)
    return case


def _token(client: TestClient, user: User) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_upload_valid_pdf_generates_safe_filename_and_never_returns_path(
    database: Session,
    client: TestClient,
) -> None:
    user = _user(database, "1001")
    case = _case(database, user)
    response = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("../../unsafe-name.pdf", b"%PDF-1.7\nsecure", "application/pdf")},
        headers=_headers(_token(client, user)),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "unsafe-name.pdf"
    assert body["mime_type"] == "application/pdf"
    assert body["status"] == "stored"
    assert body["size_bytes"] == len(b"%PDF-1.7\nsecure")
    assert "storage_path" not in body
    assert "../" not in str(body)
    document = database.scalar(select(CaseDocument))
    assert document is not None
    assert document.storage_path != "unsafe-name.pdf"
    assert document.storage_path.endswith(".pdf")
    assert Path(document.storage_path).name == document.storage_path


def test_upload_rejects_executable_mismatch_and_oversized_files(
    client: TestClient,
    database: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _user(database, "1002")
    case = _case(database, user, "SA-TEST-1002")
    token = _token(client, user)

    executable = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("payload.exe", b"MZ executable", "application/octet-stream")},
        headers=_headers(token),
    )
    assert executable.status_code == 400
    assert executable.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

    mismatch = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("not-really.png", b"%PDF-1.7\n", "image/png")},
        headers=_headers(token),
    )
    assert mismatch.status_code == 415
    assert mismatch.json()["error"]["code"] == "INVALID_FILE_SIGNATURE"

    monkeypatch.setenv("SAHAYA_UPLOAD_MAX_BYTES", "4")
    oversized = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("large.pdf", b"%PDF-1.7\ntoo large", "application/pdf")},
        headers=_headers(token),
    )
    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_case_upload_and_read_are_owner_scoped(
    database: Session,
    client: TestClient,
) -> None:
    owner = _user(database, "1003")
    other = _user(database, "1004")
    case = _case(database, owner, "SA-TEST-1003")
    owner_token = _token(client, owner)
    other_token = _token(client, other)

    upload = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("owned.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
        headers=_headers(owner_token),
    )
    assert upload.status_code == 201

    mine = client.get("/api/v1/cases/me", headers=_headers(owner_token))
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [case.id]
    detail = client.get(f"/api/v1/cases/{case.id}", headers=_headers(owner_token))
    assert detail.status_code == 200
    assert detail.json()["documents"][0]["filename"] == "owned.png"

    forbidden_upload = client.post(
        "/api/v1/cases/upload",
        data={"case_id": str(case.id)},
        files={"file": ("other.png", b"\x89PNG\r\n\x1a\nother", "image/png")},
        headers=_headers(other_token),
    )
    assert forbidden_upload.status_code == 404
    assert forbidden_upload.json()["error"]["code"] == "CASE_NOT_FOUND"
    assert client.get(f"/api/v1/cases/{case.id}", headers=_headers(other_token)).status_code == 404
    assert len(database.scalars(select(CaseDocument)).all()) == 1


def test_demo_case_returns_real_metadata_timeline_documents_and_support(
    database: Session,
    client: TestClient,
) -> None:
    seed_demo(database)
    persona = next(item for item in DEMO_PERSONAS if item.key == "user:victim:aarohi-demo")
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": persona.email, "password": persona.password},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/cases/me",
        headers=_headers(login.json()["access_token"]),
    )
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 2
    case = next(item for item in cases if item["case_number"] == "SA-DEMO-1001")
    assert case["is_demo"] is True
    assert case["category_verified"] is False
    assert case["documents"]
    assert case["timeline"]
    assert case["support_information"]
    assert all(item["is_demo"] is True for item in case["documents"])
    assert "No real" in case["summary"] or "synthetic" in case["summary"].casefold()
    detail = client.get(
        f"/api/v1/cases/{case['id']}",
        headers=_headers(login.json()["access_token"]),
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == case["id"]


def test_victim_can_start_a_private_case_without_government_verification(
    client: TestClient,
    database: Session,
) -> None:
    user = _user(database, "1099")
    response = client.post(
        "/api/v1/cases",
        json={"category": "general_support", "summary": "Private initial context."},
        headers=_headers(_token(client, user)),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "general_support"
    assert body["category_verified"] is False
    assert body["is_demo"] is False
    assert database.scalar(select(Case).where(Case.id == body["id"])) is not None
