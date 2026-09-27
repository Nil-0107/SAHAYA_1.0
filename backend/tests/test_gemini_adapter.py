"""Mocked Google Gemini adapter contract tests."""

from app.core.config import Settings
from app.integrations.gemini import GeminiAdapter, GeminiUnavailableError


def test_gemini_adapter_uses_server_key_and_server_instruction() -> None:
    captured: dict[str, object] = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return type("Response", (), {"text": "A safe supportive response."})()

    class FakeClient:
        models = FakeModels()

    def factory(*, api_key: str):
        captured["api_key"] = api_key
        return FakeClient()

    settings = Settings(
        environment="test",
        database_url="sqlite:///:memory:",
        cors_origins=(),
        gemini_api_key="test-server-key",
        gemini_model="test-model",
    )
    result = GeminiAdapter(settings, client_factory=factory).generate(
        system_instruction="SERVER_ONLY_INSTRUCTION",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
    )

    assert result == "A safe supportive response."
    assert captured["api_key"] == "test-server-key"
    assert captured["model"] == "test-model"
    assert captured["contents"] == [
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "Hi"}]},
    ]
    assert captured["config"].system_instruction == "SERVER_ONLY_INSTRUCTION"
    assert "SERVER_ONLY_INSTRUCTION" not in result


def test_gemini_adapter_fails_safely_without_key() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite:///:memory:",
        cors_origins=(),
    )
    try:
        GeminiAdapter(settings).generate(
            system_instruction="SERVER_ONLY_INSTRUCTION",
            messages=[{"role": "user", "content": "Hello"}],
        )
    except GeminiUnavailableError as error:
        assert "not configured" in str(error)
    else:
        raise AssertionError("Gemini must fail safely without a server key")
