"""Backend-only DistilBERT emotion classification supplemental signal.

This model classifies the six emotions in the DAIR.AI Emotion dataset. It is
not a distress, risk, diagnosis, or mental-health prediction model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any


CHECKPOINT_ID = "bhadresh-savani/distilbert-base-uncased-emotion"
CHECKPOINT_REVISION = "ce6f4ffcde7642ca2cac02381a16da38e5498ff7"
MODEL_DIR = Path(__file__).resolve().parent / "artifacts" / "distilbert_emotion"
EMOTION_LABELS = ("sadness", "joy", "love", "anger", "fear", "surprise")


class EmotionModelError(RuntimeError):
    """Raised when the supplemental emotion model cannot load or infer."""


@dataclass(frozen=True, slots=True)
class EmotionPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
            "model_version": self.model_version,
        }


class DistilBertEmotionClassifier:
    """One process-local, CPU inference instance for the bundled checkpoint."""

    def __init__(self, tokenizer: Any, model: Any, torch_module: Any) -> None:
        self.tokenizer = tokenizer
        self.model = model
        self.torch = torch_module

    @classmethod
    def load(cls) -> "DistilBertEmotionClassifier":
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                str(MODEL_DIR),
                local_files_only=True,
            )
            model.eval()
        except Exception as exc:
            raise EmotionModelError("DistilBERT emotion model is unavailable") from exc

        id2label = model.config.id2label
        configured_labels = tuple(
            id2label.get(index, id2label.get(str(index), ""))
            for index in range(len(EMOTION_LABELS))
        )
        if configured_labels != EMOTION_LABELS:
            raise EmotionModelError("DistilBERT emotion model has an incompatible label contract")
        return cls(tokenizer, model, torch)

    def predict(self, text: str) -> EmotionPrediction:
        if not isinstance(text, str) or not text.strip():
            raise EmotionModelError("Emotion text must be a non-empty string")
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            with self.torch.inference_mode():
                logits = self.model(**inputs).logits
                probabilities = self.torch.softmax(logits, dim=-1)[0].tolist()
            if len(probabilities) != len(EMOTION_LABELS):
                raise ValueError("unexpected number of emotion classes")
            values = [float(value) for value in probabilities]
            index = max(range(len(values)), key=values.__getitem__)
        except EmotionModelError:
            raise
        except Exception as exc:
            raise EmotionModelError("DistilBERT emotion inference is unavailable") from exc

        return EmotionPrediction(
            label=EMOTION_LABELS[index],
            confidence=values[index],
            probabilities={label: values[i] for i, label in enumerate(EMOTION_LABELS)},
            model_version=CHECKPOINT_ID,
        )


_lock = Lock()
_classifier: DistilBertEmotionClassifier | None = None
_load_error: EmotionModelError | None = None


def get_emotion_classifier() -> DistilBertEmotionClassifier:
    global _classifier, _load_error
    if _classifier is None:
        with _lock:
            if _classifier is None:
                if _load_error is not None:
                    raise _load_error
                try:
                    _classifier = DistilBertEmotionClassifier.load()
                except EmotionModelError as exc:
                    _load_error = exc
                    raise
    return _classifier
