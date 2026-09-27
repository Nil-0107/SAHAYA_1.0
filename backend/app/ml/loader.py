"""Safe, lazy singleton loading for the supplied local ML artifacts."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

from joblib import load


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
VECTORIZER_PATH = ARTIFACT_DIR / "tfidf_vectorizer.joblib"
MODEL_PATH = ARTIFACT_DIR / "logistic_regression_emotion_model.joblib"
VECTORIZER_ARTIFACT_ID = VECTORIZER_PATH.name
MODEL_ARTIFACT_ID = MODEL_PATH.name

_lock = Lock()
_vectorizer: Any | None = None
_model: Any | None = None


class MLArtifactError(RuntimeError):
    """Raised when a required artifact cannot be safely loaded or validated."""


def get_vectorizer() -> Any:
    global _vectorizer
    if _vectorizer is None:
        with _lock:
            if _vectorizer is None:
                _vectorizer = _load_artifact(
                    VECTORIZER_PATH,
                    artifact_name="ML vectorizer",
                    validator=_validate_vectorizer,
                )
    return _vectorizer


def get_model() -> Any:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = _load_artifact(
                    MODEL_PATH,
                    artifact_name="ML classifier",
                    validator=_validate_model,
                )
    return _model


def _load_artifact(path: Path, *, artifact_name: str, validator: Any) -> Any:
    if not path.is_file():
        raise MLArtifactError(f"{artifact_name} artifact is unavailable")
    try:
        artifact = load(path)
        validator(artifact)
    except MLArtifactError:
        raise
    except Exception as exc:
        raise MLArtifactError(f"{artifact_name} artifact could not be loaded") from exc
    return artifact


def _validate_vectorizer(vectorizer: Any) -> None:
    if not callable(getattr(vectorizer, "transform", None)):
        raise MLArtifactError("ML vectorizer artifact is incompatible")
    if not hasattr(vectorizer, "vocabulary_") or not hasattr(vectorizer, "idf_"):
        raise MLArtifactError("ML vectorizer artifact is not fitted")
    if getattr(vectorizer, "max_features", None) != 5000 or len(getattr(vectorizer, "vocabulary_", {})) != 5000:
        raise MLArtifactError("ML vectorizer feature contract is incompatible")


def _validate_model(model: Any) -> None:
    if not callable(getattr(model, "predict", None)):
        raise MLArtifactError("ML classifier artifact is incompatible")
    if not hasattr(model, "classes_") or not hasattr(model, "coef_"):
        raise MLArtifactError("ML classifier artifact is not fitted")
    try:
        classes = {int(value) for value in model.classes_}
    except (TypeError, ValueError) as exc:
        raise MLArtifactError("ML classifier class contract is incompatible") from exc
    if classes != {0, 1, 2, 3, 4, 5} or getattr(model, "n_features_in_", None) != 5000:
        raise MLArtifactError("ML classifier feature/class contract is incompatible")
