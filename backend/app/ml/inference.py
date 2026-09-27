"""Server-side inference around the supplied fitted ML artifacts.

The artifacts expose numeric class IDs only. This module intentionally does not
assign semantic labels or interpret predictions as risk, diagnosis, or safety
signals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.ml import loader
from app.ml.loader import MLArtifactError


@dataclass(frozen=True, slots=True)
class MLPrediction:
    class_id: int
    label: str | None
    confidence: float | None
    model_version: str


class MLInputError(ValueError):
    """Raised when inference input is not a usable non-empty text string."""


class MLPredictionError(RuntimeError):
    """Raised when the loaded artifacts fail during inference."""


class MLService:
    def predict(self, text: str) -> MLPrediction:
        if not isinstance(text, str) or not text.strip():
            raise MLInputError("Check-in text must be a non-empty string")

        try:
            vectorizer = loader.get_vectorizer()
            model = loader.get_model()
            features = vectorizer.transform([text])
        except MLArtifactError:
            raise
        except Exception as exc:
            raise MLPredictionError("ML prediction is temporarily unavailable") from exc

        classes = getattr(model, "classes_", None)
        if classes is None:
            raise MLPredictionError("ML prediction is temporarily unavailable")

        predict_proba = getattr(model, "predict_proba", None)
        if callable(predict_proba):
            probabilities = self._probabilities(predict_proba, features)
            try:
                if len(probabilities) != len(classes):
                    raise ValueError
                predicted_index = max(range(len(probabilities)), key=probabilities.__getitem__)
                predicted_class = classes[predicted_index]
            except Exception as exc:
                raise MLPredictionError("ML prediction returned an invalid class") from exc
            confidence = probabilities[predicted_index]
        else:
            confidence = None
            predicted_class = self._class_from_predict(model, features)

        try:
            class_value = int(predicted_class)
        except (TypeError, ValueError) as exc:
            raise MLPredictionError("ML prediction returned an invalid class") from exc

        return MLPrediction(
            class_id=class_value,
            label=None,
            confidence=confidence,
            model_version=loader.MODEL_ARTIFACT_ID,
        )

    @staticmethod
    def _probabilities(predict_proba: Any, features: Any) -> list[float]:
        try:
            probabilities = predict_proba(features)
            if len(probabilities) != 1:
                raise ValueError
            row = probabilities[0]
            if len(row) == 0:
                raise ValueError
            values = [float(value) for value in row]
        except Exception as exc:
            raise MLPredictionError("ML prediction is temporarily unavailable") from exc

        if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in values):
            raise MLPredictionError("ML prediction returned invalid probabilities")
        return values

    @staticmethod
    def _class_from_predict(model: Any, features: Any) -> Any:
        try:
            predictions = model.predict(features)
            if len(predictions) != 1:
                raise ValueError
            return predictions[0]
        except Exception as exc:
            raise MLPredictionError("ML prediction is temporarily unavailable") from exc


# Kept as an explicit compatibility alias for existing service imports.
WellbeingService = MLService
