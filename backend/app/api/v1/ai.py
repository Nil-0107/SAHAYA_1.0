"""Authenticated server-side AI support API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_ready_user
from app.core.rate_limit import RateLimitExceeded, enforce_rate_limit
from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import AIChatMessageResponse, AIChatRequest, AIChatResponse, AIVoiceResponse
from app.integrations.gemini import GeminiAdapter, GeminiUnavailableError
from app.services.ai_service import AIService, AIServiceError


router = APIRouter(prefix="/ai", tags=["ai"])


def _raise_service_error(error: AIServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


def _message_response(message) -> AIChatMessageResponse:
    return AIChatMessageResponse.model_validate(message)


@router.post("/chat", response_model=AIChatResponse, status_code=status.HTTP_200_OK)
def chat(
    payload: AIChatRequest,
    request: Request,
    user: User = Depends(get_current_ready_user),
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AIChatResponse:
    try:
        client = request.client.host if request.client else "unknown"
        enforce_rate_limit(f"ai:{user.id}:{client}", limit=30, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": str(exc)}) from exc
    try:
        result = AIService(database, settings).chat(
            user=user,
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except AIServiceError as error:
        _raise_service_error(error)
    return AIChatResponse(
        conversation_id=result.conversation.id,
        conversation_status=result.conversation.status,
        source=result.source,
        model_version=result.model_version,
        immediate_danger=result.immediate_danger,
        user_message=_message_response(result.user_message),
        assistant_message=_message_response(result.assistant_message),
    )


@router.get("/health")
def ai_health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    return {**GeminiAdapter(settings).health(), "model": settings.gemini_model}


@router.post("/voice/transcribe", response_model=AIVoiceResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
    user: User = Depends(get_current_ready_user),
    settings: Settings = Depends(get_settings),
) -> AIVoiceResponse:
    allowed = {"audio/webm", "audio/ogg", "audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/aac"}
    mime_type = (file.content_type or "").split(";", 1)[0].lower()
    if mime_type not in allowed:
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_AUDIO", "message": "Use a browser-supported WebM, OGG, WAV, MP3, M4A, or AAC recording."})
    audio = await file.read(10 * 1024 * 1024 + 1)
    await file.close()
    if len(audio) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "AUDIO_TOO_LARGE", "message": "Audio exceeds the 10 MB limit."})
    if not audio:
        raise HTTPException(status_code=400, detail={"code": "EMPTY_AUDIO", "message": "The audio recording is empty."})
    system = "You are a transcription component for SAHAYA. Transcribe only the user's spoken words. Do not infer, diagnose, summarize, or add facts."
    try:
        transcript = GeminiAdapter(settings).transcribe_audio(system_instruction=system, audio=audio, mime_type=mime_type)
    except GeminiUnavailableError as error:
        raise HTTPException(status_code=503, detail={"code": "VOICE_TRANSCRIPTION_UNAVAILABLE", "message": str(error)}) from error
    return AIVoiceResponse(transcript=transcript, source="gemini", model_version=settings.gemini_model)


@router.post("/voice/speak")
def speak_text(payload: dict, user: User = Depends(get_current_ready_user)):
    text = str(payload.get("text", "")).strip()
    if not text or len(text) > 4000:
        raise HTTPException(status_code=422, detail={"code": "TTS_TEXT_INVALID", "message": "Text must be between 1 and 4000 characters"})
    try:
        import pyttsx3
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="sahaya-tts-")
        Path(path).unlink(missing_ok=True)
        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
        engine.stop()
        return FileResponse(path, media_type="audio/wav", filename="sahaya-response.wav", background=None)
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "TTS_UNAVAILABLE", "message": "Text-to-speech is unavailable on this server"}) from exc
