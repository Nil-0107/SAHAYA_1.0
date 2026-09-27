"""Application configuration.

The demo seed deliberately has no FastAPI route and is invoked only by its
module command. Environment validation is kept here so the command cannot be
used in a production deployment accidentally.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ALLOWED_DEMO_ENVIRONMENTS = frozenset({"development", "local", "test"})
_EPHEMERAL_DEVELOPMENT_JWT_SECRET = secrets.token_urlsafe(64)


class DemoSeedEnvironmentError(RuntimeError):
    """Raised when the controlled seed is requested in an unsafe environment."""


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    database_url: str
    cors_origins: tuple[str, ...]
    jwt_secret_key: str = field(default="", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "saathi-api"
    jwt_audience: str = "saathi-web"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    refresh_cookie_secure: bool = False
    otp_secret_encryption_key: str = field(default="", repr=False)
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = "gemini-2.5-flash"
    upload_directory: str = ""
    upload_max_bytes: int = 10 * 1024 * 1024
    otp_totp_interval_seconds: int = 30
    otp_totp_digits: int = 6
    otp_totp_valid_window: int = 1
    otp_expiry_minutes: int = 5
    otp_start_cooldown_seconds: int = 30
    otp_resend_cooldown_seconds: int = 60
    otp_window_max_requests: int = 5
    otp_max_verify_attempts: int = 5

    @classmethod
    def from_environment(cls) -> "Settings":
        backend_root = Path(__file__).resolve().parents[2]
        load_dotenv(backend_root / ".env", override=False)
        environment = os.getenv("SAATHI_ENV", "").strip().lower()
        default_origins = (
            "http://localhost:5173,http://127.0.0.1:5173"
            if environment in {"development", "local", "test"}
            else ""
        )
        cors_origins = tuple(
            origin.strip()
            for origin in os.getenv("SAATHI_CORS_ORIGINS", default_origins).split(",")
            if origin.strip()
        )
        jwt_secret_key = os.getenv("SAATHI_JWT_SECRET_KEY", "").strip()
        otp_secret_encryption_key = os.getenv(
            "SAATHI_OTP_SECRET_ENCRYPTION_KEY", ""
        ).strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        upload_directory = os.getenv("SAATHI_UPLOAD_DIRECTORY", "").strip() or str(backend_root / "uploads")
        upload_max_bytes = min(
            int(os.getenv("SAATHI_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))),
            10 * 1024 * 1024,
        )
        if environment == "production":
            if not jwt_secret_key:
                raise RuntimeError("SAATHI_JWT_SECRET_KEY is required in production")
            if os.getenv("SAATHI_REFRESH_COOKIE_SECURE", "true").strip().lower() not in {"1", "true", "yes"}:
                raise RuntimeError("SAATHI_REFRESH_COOKIE_SECURE must be true in production")
            if os.getenv("SAATHI_JWT_ALGORITHM", "HS256").strip() != "HS256":
                raise RuntimeError("Only HS256 is allowed for the configured JWT algorithm")
        if not jwt_secret_key:
            jwt_secret_key = _EPHEMERAL_DEVELOPMENT_JWT_SECRET
        if not otp_secret_encryption_key:
            otp_secret_encryption_key = jwt_secret_key
        return cls(
            environment=environment,
            database_url=os.getenv(
                "SAATHI_DATABASE_URL",
                f"sqlite:///{backend_root / 'saathi.db'}",
            ),
            cors_origins=cors_origins,
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=os.getenv("SAATHI_JWT_ALGORITHM", "HS256").strip(),
            jwt_issuer=os.getenv("SAATHI_JWT_ISSUER", "saathi-api").strip(),
            jwt_audience=os.getenv("SAATHI_JWT_AUDIENCE", "saathi-web").strip(),
            access_token_minutes=int(os.getenv("SAATHI_ACCESS_TOKEN_MINUTES", "15")),
            refresh_token_days=int(os.getenv("SAATHI_REFRESH_TOKEN_DAYS", "7")),
            refresh_cookie_secure=os.getenv(
                "SAATHI_REFRESH_COOKIE_SECURE",
                "true" if environment == "production" else "false",
            ).strip().lower()
            in {"1", "true", "yes"},
            otp_secret_encryption_key=otp_secret_encryption_key,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            upload_directory=upload_directory,
            upload_max_bytes=upload_max_bytes,
            otp_totp_interval_seconds=int(
                os.getenv("SAATHI_OTP_TOTP_INTERVAL_SECONDS", "30")
            ),
            otp_totp_digits=int(os.getenv("SAATHI_OTP_TOTP_DIGITS", "6")),
            otp_totp_valid_window=int(
                os.getenv("SAATHI_OTP_TOTP_VALID_WINDOW", "1")
            ),
            otp_expiry_minutes=int(os.getenv("SAATHI_OTP_EXPIRY_MINUTES", "5")),
            otp_start_cooldown_seconds=int(
                os.getenv("SAATHI_OTP_START_COOLDOWN_SECONDS", "30")
            ),
            otp_resend_cooldown_seconds=int(
                os.getenv("SAATHI_OTP_RESEND_COOLDOWN_SECONDS", "60")
            ),
            otp_window_max_requests=int(
                os.getenv("SAATHI_OTP_WINDOW_MAX_REQUESTS", "5")
            ),
            otp_max_verify_attempts=int(
                os.getenv("SAATHI_OTP_MAX_VERIFY_ATTEMPTS", "5")
            ),
        )

    def require_demo_seed_allowed(self) -> None:
        if self.environment not in ALLOWED_DEMO_ENVIRONMENTS:
            allowed = ", ".join(sorted(ALLOWED_DEMO_ENVIRONMENTS))
            raise DemoSeedEnvironmentError(
                "Demo seeding is blocked outside local/development/test "
                f"environments (SAATHI_ENV={self.environment!r}). Allowed: {allowed}."
            )

    def reject_obvious_production_database(self) -> None:
        """Second safety check for a production-looking database identifier."""
        normalized = self.database_url.casefold()
        production_markers = (
            "saathi_production",
            "saathi-prod",
            "saathi.prod",
            "prod.db",
            "production.db",
            "/production/",
        )
        if any(marker in normalized for marker in production_markers):
            raise DemoSeedEnvironmentError(
                "Demo seeding is blocked for a production-looking database URL."
            )


def get_settings() -> Settings:
    return Settings.from_environment()
