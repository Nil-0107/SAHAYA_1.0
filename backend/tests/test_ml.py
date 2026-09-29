"""Tests for the supplied local ML artifacts and inference boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ml import loader
from app.ml.inference import MLInputError, MLPredictionError, MLService
from app.ml.loader import MLArtifactError


def test_vectorizer_and_model_load_once() -> None:
    loader._vectorizer = None
    loader._model = None

    vectorizer = loader.get_vectorizer()
    model = loader.get_model()

    assert vectorizer.__class__.__name__ == "TfidfVectorizer"
    assert model.__class__.__name__ == "LogisticRegression"
    assert loader.get_vectorizer() is vectorizer
    assert loader.get_model() is model


def test_distilbert_emotion_inference_returns_all_six_dataset_classes() -> None:
    pytest.importorskip("torch")
    pytest.importorskip("transformers")

    from app.ml.emotion import CHECKPOINT_ID, EMOTION_LABELS, get_emotion_classifier

    result = get_emotion_classifier().predict("I feel nervous and afraid about what may happen next.")

    assert result.model_version == CHECKPOINT_ID
    assert result.label in EMOTION_LABELS
    assert tuple(result.probabilities) == EMOTION_LABELS
    assert len(result.probabilities) == 6
    assert sum(result.probabilities.values()) == pytest.approx(1.0, abs=1e-5)
    assert 0.0 <= result.confidence <= 1.0


def test_valid_text_returns_numeric_class_unknown_label_and_confidence() -> None:
    result = MLService().predict("I am uncertain about what happened")

    assert result.class_id in {0, 1, 2, 3, 4, 5}
    assert result.label is None
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0
    assert result.model_version == "logistic_regression_emotion_model.joblib"


def test_empty_text_is_rejected() -> None:
    with pytest.raises(MLInputError, match="non-empty string"):
        MLService().predict("   ")


@pytest.mark.parametrize("value", [None, 42, b"bytes", {"text": "hello"}])
def test_invalid_input_is_rejected(value: object) -> None:
    with pytest.raises(MLInputError, match="non-empty string"):
        MLService().predict(value)  # type: ignore[arg-type]


def test_prediction_uses_probability_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVectorizer:
        def transform(self, texts: list[str]):
            assert texts == ["hello"]
            return object()

    class FakeModel:
        classes_ = [10, 11]

        def predict_proba(self, features: object):
            assert features is not None
            return [[0.25, 0.75]]

    monkeypatch.setattr(loader, "get_vectorizer", lambda: FakeVectorizer())
    monkeypatch.setattr(loader, "get_model", lambda: FakeModel())

    result = MLService().predict("hello")

    assert result.class_id == 11
    assert result.label is None
    assert result.confidence == pytest.approx(0.75)
    assert result.model_version == loader.MODEL_ARTIFACT_ID


def test_prediction_confidence_is_null_without_probability(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVectorizer:
        def transform(self, texts: list[str]):
            return object()

    class FakeModel:
        classes_ = [10, 11]

        def predict(self, features: object):
            return [10]

    monkeypatch.setattr(loader, "get_vectorizer", lambda: FakeVectorizer())
    monkeypatch.setattr(loader, "get_model", lambda: FakeModel())

    result = MLService().predict("hello")

    assert result.class_id == 10
    assert result.label is None
    assert result.confidence is None


def test_prediction_failure_returns_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenVectorizer:
        def transform(self, texts: list[str]):
            raise RuntimeError("internal vectorizer details")

    monkeypatch.setattr(loader, "get_vectorizer", lambda: BrokenVectorizer())
    monkeypatch.setattr(loader, "get_model", lambda: object())

    with pytest.raises(MLPredictionError, match="temporarily unavailable") as error:
        MLService().predict("hello")
    assert "internal vectorizer details" not in str(error.value)


def test_missing_artifact_returns_safe_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "_vectorizer", None)
    monkeypatch.setattr(loader, "VECTORIZER_PATH", tmp_path / "missing.joblib")

    with pytest.raises(MLArtifactError, match="unavailable") as error:
        loader.get_vectorizer()
    assert "missing.joblib" not in str(error.value)


def test_corrupted_artifact_returns_safe_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    corrupted = tmp_path / "corrupted.joblib"
    corrupted.write_bytes(b"not a joblib artifact")
    monkeypatch.setattr(loader, "_vectorizer", None)
    monkeypatch.setattr(loader, "VECTORIZER_PATH", corrupted)

    with pytest.raises(MLArtifactError, match="could not be loaded") as error:
        loader.get_vectorizer()
    assert "corrupted.joblib" not in str(error.value)
    assert "Traceback" not in str(error.value)


def test_incompatible_artifact_returns_safe_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    incompatible = tmp_path / "incompatible.joblib"
    import joblib

    joblib.dump(object(), incompatible)
    monkeypatch.setattr(loader, "_vectorizer", None)
    monkeypatch.setattr(loader, "VECTORIZER_PATH", incompatible)

    with pytest.raises(MLArtifactError, match="incompatible"):
        loader.get_vectorizer()
