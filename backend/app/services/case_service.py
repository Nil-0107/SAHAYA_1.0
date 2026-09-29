"""Owner-scoped case and secure document service."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_document import CaseDocument, DocumentStatus
from app.models.user import Role, User
from app.models.notification import Notification


class CaseServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class CaseService:
    _allowed_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }

    def __init__(self, database: Session, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self.include_demo = settings.demo_data_enabled

    def list_for_user(self, *, user: User) -> list[Case]:
        query = select(Case).where(Case.owner_user_id == user.id)
        if not self.include_demo:
            query = query.where(Case.is_demo.is_(False))
        return list(self.database.scalars(query.order_by(Case.created_at.desc(), Case.id.desc())))

    def create_for_user(self, *, user: User, category: str, summary: str | None) -> Case:
        normalized_category = category.strip().casefold()
        if not normalized_category:
            raise CaseServiceError(422, "CASE_CATEGORY_INVALID", "Case category is required")
        case = Case(
            owner_user_id=user.id,
            case_number=f"SA-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}",
            category=normalized_category,
            category_verified=False,
            status="open",
            stage="intake",
            summary=(summary or "").strip() or None,
        )
        self.database.add(case)
        try:
            self.database.flush()
            self.database.add(
                AuditLog(
                    actor_user_id=user.id,
                    action="CASE_CREATED",
                    resource_type="case",
                    resource_id=str(case.id),
                    metadata_json={"category": normalized_category, "verification_status": "not_verified"},
                )
            )
            self.database.commit()
            self.database.refresh(case)
            return case
        except Exception:
            self.database.rollback()
            raise CaseServiceError(503, "CASE_SAVE_FAILED", "The case could not be saved")

    def get_for_user(self, *, user: User, case_id: int) -> Case:
        query = select(Case).where(Case.id == case_id, Case.owner_user_id == user.id)
        if not self.include_demo:
            query = query.where(Case.is_demo.is_(False))
        case = self.database.scalar(query)
        if case is None:
            raise CaseServiceError(404, "CASE_NOT_FOUND", "Case not found")
        return case

    async def upload_document(
        self,
        *,
        user: User,
        case_id: int | None,
        upload: UploadFile,
    ) -> CaseDocument:
        case = self.get_for_user(user=user, case_id=case_id) if case_id else None
        if case is None:
            case = self.create_for_user(user=user, category="uploaded_document", summary="Case created from uploaded document")
        original_name = (upload.filename or "document").replace("\\", "/")
        display_name = Path(original_name).name
        display_name = "".join(character for character in display_name if character.isprintable()).strip()
        display_name = display_name[:255] or "document"
        extension = Path(display_name).suffix.casefold()
        expected_mime = self._allowed_types.get(extension)
        if expected_mime is None:
            raise CaseServiceError(400, "UNSUPPORTED_FILE_TYPE", "Only PDF, JPG, JPEG, and PNG files are accepted")
        declared_mime = (upload.content_type or "").split(";", 1)[0].casefold()
        if declared_mime != expected_mime:
            raise CaseServiceError(400, "INVALID_FILE_TYPE", "The file MIME type does not match its extension")

        content = bytearray()
        try:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                content.extend(chunk)
                if len(content) > self.settings.upload_max_bytes:
                    raise CaseServiceError(413, "FILE_TOO_LARGE", "The file exceeds the 10 MB limit")
        finally:
            await upload.close()

        if not content:
            raise CaseServiceError(400, "EMPTY_FILE", "The uploaded file is empty")
        if not self._matches_signature(extension, bytes(content)):
            raise CaseServiceError(415, "INVALID_FILE_SIGNATURE", "The file content does not match the allowed file type")

        upload_root = Path(self.settings.upload_directory).expanduser().resolve()
        upload_root.mkdir(parents=True, exist_ok=True)
        safe_name = f"{secrets.token_urlsafe(24)}{extension}"
        target = (upload_root / safe_name).resolve()
        if target.parent != upload_root:
            raise CaseServiceError(400, "INVALID_UPLOAD_PATH", "The upload path is invalid")
        try:
            target.write_bytes(bytes(content))
            document = CaseDocument(
                case_id=case.id,
                owner_user_id=user.id,
                filename=display_name,
                mime_type=expected_mime,
                storage_path=safe_name,
                status=DocumentStatus.STORED,
                extracted_json={
                    "size_bytes": len(content),
                    "source": "user_upload",
                    "verification_status": "not_verified",
                },
                uploaded_at=datetime.now(timezone.utc),
            )
            self.database.add(document)
            self.database.flush()
            self.database.add(
                AuditLog(
                    actor_user_id=user.id,
                    action="CASE_DOCUMENT_UPLOADED",
                    resource_type="case",
                    resource_id=str(case.id),
                    metadata_json={
                        "document_id": str(document.id),
                        "mime_type": expected_mime,
                        "size_bytes": len(content),
                        "verification_status": "not_verified",
                    },
                )
            )
            # Notify the user's authorised administrative scope and active counsellor assignments.
            recipients = list(self.database.scalars(select(User).where(User.id != user.id, User.is_demo.is_(False))))
            for recipient in recipients:
                in_scope = False
                if recipient.role == Role.NATIONAL_ADMIN:
                    in_scope = True
                elif recipient.role == Role.STATE_ADMIN and user.state_id is not None and recipient.state_id == user.state_id:
                    in_scope = True
                elif recipient.role == Role.DISTRICT_ADMIN and user.district_id is not None and recipient.district_id == user.district_id:
                    in_scope = True
                elif recipient.role == Role.COUNSELLOR:
                    from app.models.case_assignment import CaseAssignment
                    in_scope = self.database.scalar(select(CaseAssignment.id).where(CaseAssignment.case_id == case.id, CaseAssignment.assignee_user_id == recipient.id, CaseAssignment.active.is_(True))) is not None
                if in_scope:
                    self.database.add(Notification(user_id=recipient.id, case_id=case.id, type="case_document", title="New case document uploaded", message=f"A case document was uploaded for case {case.case_number} by an authorised user."))
            self.database.add(Notification(user_id=user.id, case_id=case.id, type="case_document", title="Case document uploaded", message=f"{display_name} was uploaded successfully."))
            self.database.commit()
            self.database.refresh(document)
            return document
        except Exception:
            self.database.rollback()
            target.unlink(missing_ok=True)
            raise

    @staticmethod
    def _matches_signature(extension: str, content: bytes) -> bool:
        if extension == ".pdf":
            return content.startswith(b"%PDF-")
        if extension in {".jpg", ".jpeg"}:
            return content.startswith(b"\xff\xd8\xff")
        if extension == ".png":
            return content.startswith(b"\x89PNG\r\n\x1a\n")
        return False
