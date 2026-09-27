"""Server-only Google Gemini adapter with SDK and REST fallback."""

from __future__ import annotations

import base64
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from app.core.config import Settings


class GeminiUnavailableError(RuntimeError):
    """Raised when Gemini cannot provide a response."""


class GeminiAdapter:
    def __init__(self, settings: Settings, client_factory: Callable[..., Any] | None = None) -> None:
        self.settings = settings
        self.client_factory = client_factory

    def generate(self, *, system_instruction: str, messages: Sequence[dict[str, str]]) -> str:
        if not self.settings.gemini_api_key:
            raise GeminiUnavailableError("Gemini support is not configured. Set GEMINI_API_KEY in backend/.env and restart the backend.")
        try:
            return self._sdk_generate(system_instruction=system_instruction, messages=messages)
        except GeminiUnavailableError:
            raise
        except Exception as sdk_error:
            try:
                return self._rest_generate(system_instruction=system_instruction, messages=messages)
            except Exception as rest_error:
                raise GeminiUnavailableError(
                    "Gemini request failed. Check GEMINI_API_KEY, GEMINI_MODEL, network access, and the Google API key's Generative Language API permissions."
                ) from rest_error

    def transcribe_audio(self, *, system_instruction: str, audio: bytes, mime_type: str) -> str:
        if not self.settings.gemini_api_key:
            raise GeminiUnavailableError("Gemini support is not configured. Set GEMINI_API_KEY in backend/.env and restart the backend.")
        prompt = "Transcribe the supplied audio faithfully. Return only the spoken words. Do not add facts or commentary."
        try:
            from google import genai
            from google.genai import types
            factory = self.client_factory or genai.Client
            client = factory(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt), types.Part(inline_data=types.Blob(data=audio, mime_type=mime_type))])],
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.0),
            )
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
        except Exception:
            pass
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(audio).decode("ascii")}},
            ]}],
            "generationConfig": {"temperature": 0.0},
        }
        response = httpx.post(url, params={"key": self.settings.gemini_api_key}, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        text = self._extract_rest_text(data)
        if not text:
            raise GeminiUnavailableError("Gemini returned no transcription")
        return text

    def _sdk_generate(self, *, system_instruction: str, messages: Sequence[dict[str, str]]) -> str:
        if self.client_factory is not None:
            factory = self.client_factory
        else:
            from google import genai
            factory = genai.Client
        client = factory(api_key=self.settings.gemini_api_key)
        contents = [{
            "role": "model" if message["role"] == "assistant" else "user",
            "parts": [{"text": message["content"]}],
        } for message in messages]
        if self.client_factory is not None:
            from types import SimpleNamespace
            config = SimpleNamespace(system_instruction=system_instruction, temperature=0.2)
        else:
            from google.genai import types
            config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=contents,
            config=config,
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Gemini returned no text")
        return text.strip()

    def _rest_generate(self, *, system_instruction: str, messages: Sequence[dict[str, str]]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        contents = [{
            "role": "model" if message["role"] == "assistant" else "user",
            "parts": [{"text": message["content"]}],
        } for message in messages]
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.2},
        }
        response = httpx.post(url, params={"key": self.settings.gemini_api_key}, json=payload, timeout=45.0)
        response.raise_for_status()
        text = self._extract_rest_text(response.json())
        if not text:
            raise GeminiUnavailableError("Gemini returned no text")
        return text

    @staticmethod
    def _extract_rest_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
        return "\n".join(str(part.get("text", "")) for part in parts if part.get("text")).strip()
