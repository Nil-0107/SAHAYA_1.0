"""Authenticated, ownership-scoped well-being check-in workflows."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.inference import MLInputError, MLPredictionError, MLService
from app.ml.loader import MLArtifactError
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.checkin import Checkin, CheckinAnalysisStatus
from app.models.user import Role, User
from app.models.notification import Notification


class CheckinServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class CreatedCheckin:
    record: Checkin
    model_version: str


class CheckinService:
    def __init__(self, database: Session, ml_service: MLService | None = None, *, include_demo: bool = True) -> None:
        self.database = database
        self.ml_service = ml_service or MLService()
        self.include_demo = include_demo

    def create(
        self,
        *,
        user: User,
        text: str,
        case_id: int | None = None,
    ) -> CreatedCheckin:
        case = self._owned_case(user, case_id)
        try:
            prediction = self.ml_service.predict(text)
        except MLInputError as exc:
            raise CheckinServiceError(422, "CHECKIN_INVALID", str(exc)) from exc
        except (MLArtifactError, MLPredictionError) as exc:
            raise CheckinServiceError(
                503,
                "CHECKIN_ANALYSIS_UNAVAILABLE",
                "Check-in analysis is temporarily unavailable",
            ) from exc

        record = Checkin(
            user_id=user.id,
            case_id=case.id if case else None,
            text=text,
            analysis_status=CheckinAnalysisStatus.COMPLETED,
            predicted_class=prediction.class_id,
            predicted_label=prediction.label,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            emotion_result=prediction.emotion.as_dict() if prediction.emotion is not None else None,
        )
        self.database.add(record)
        try:
            self.database.flush()
            self.database.add(
                AuditLog(
                    actor_user_id=user.id,
                    action="CHECKIN_CREATED",
                    resource_type="checkin",
                    resource_id=str(record.id),
                    metadata_json={
                        "class_id": prediction.class_id,
                        "confidence": prediction.confidence,
                        "model_version": prediction.model_version,
                        "case_linked": case is not None,
                    },
                )
            )
            recipients = list(self.database.scalars(select(User).where(User.id != user.id, User.is_demo.is_(False))))
            for recipient in recipients:
                in_scope = (
                    recipient.role == Role.NATIONAL_ADMIN
                    or (recipient.role == Role.STATE_ADMIN and user.state_id is not None and recipient.state_id == user.state_id)
                    or (recipient.role == Role.DISTRICT_ADMIN and user.district_id is not None and recipient.district_id == user.district_id)
                )
                if case is not None and recipient.role == Role.COUNSELLOR:
                    from app.models.case_assignment import CaseAssignment
                    in_scope = self.database.scalar(select(CaseAssignment.id).where(CaseAssignment.case_id == case.id, CaseAssignment.assignee_user_id == recipient.id, CaseAssignment.active.is_(True))) is not None
                if in_scope:
                    self.database.add(Notification(user_id=recipient.id, case_id=case.id if case else None, type="wellbeing_checkin", title="New well-being check-in", message="A new well-being check-in is available within your authorised support scope."))
            self.database.commit()
            self.database.refresh(record)
        except Exception:
            self.database.rollback()
            raise CheckinServiceError(
                503,
                "CHECKIN_SAVE_FAILED",
                "The check-in could not be saved",
            ) from None

        return CreatedCheckin(record=record, model_version=prediction.model_version)

    def list_for_user(self, *, user: User) -> list[Checkin]:
        return list(
            self.database.scalars(
            select(Checkin)
                .where(Checkin.user_id == user.id, *(() if self.include_demo else (Checkin.is_demo.is_(False),)))
                .order_by(Checkin.created_at.desc(), Checkin.id.desc())
            )
        )

    def get_for_user(self, *, user: User, checkin_id: int) -> Checkin:
        record = self.database.scalar(
            select(Checkin).where(
                Checkin.id == checkin_id,
                Checkin.user_id == user.id,
                *(() if self.include_demo else (Checkin.is_demo.is_(False),)),
            )
        )
        if record is None:
            raise CheckinServiceError(404, "CHECKIN_NOT_FOUND", "Check-in not found")
        return record

    def _owned_case(self, user: User, case_id: int | None) -> Case | None:
        if case_id is None:
            return None
        case = self.database.scalar(
            select(Case).where(
                Case.id == case_id,
                Case.owner_user_id == user.id,
                *(() if self.include_demo else (Case.is_demo.is_(False),)),
            )
        )
        if case is None:
            raise CheckinServiceError(404, "CASE_NOT_FOUND", "Case not found")
        return case
