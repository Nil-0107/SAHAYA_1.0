from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Settings
from app.main import app, create_app


def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_health_alias() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_restricted_cors_preflight() -> None:
    test_app = create_app(
        Settings(
            environment="test",
            database_url="sqlite:///:memory:",
            cors_origins=("http://localhost:5173",),
        )
    )
    response = TestClient(test_app).options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "http://localhost:5173" not in response.headers.get(
        "access-control-allow-origin", ""
    ).split(", ")[1:]

    blocked = TestClient(test_app).get(
        "/api/v1/health",
        headers={"Origin": "https://untrusted.example"},
    )
    assert blocked.status_code == 200
    assert "access-control-allow-origin" not in blocked.headers


def test_unknown_route_uses_structured_error() -> None:
    response = TestClient(app).get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "details": [],
        }
    }


def test_validation_error_uses_structured_error() -> None:
    class TestPayload(BaseModel):
        required_value: str

    test_app = create_app(
        Settings(
            environment="test",
            database_url="sqlite:///:memory:",
            cors_origins=(),
        )
    )

    @test_app.post("/_test/validation")
    def validation_endpoint(payload: TestPayload) -> dict[str, str]:
        return {"value": payload.required_value}

    response = TestClient(test_app).post("/_test/validation", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert body["error"]["details"][0]["location"] == ["body", "required_value"]


def test_method_error_uses_structured_error() -> None:
    response = TestClient(app).post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
