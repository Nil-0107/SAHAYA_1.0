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
    jwt_issuer: str = "sahaya-api"
    jwt_audience: str = "sahaya-web"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    refresh_cookie_secure: bool = False
    otp_secret_encryption_key: str = field(default="", repr=False)
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = "gemini-3.8-flash"
    demo_data_enabled: bool = False
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
        environment = os.getenv("SAHAYA_ENV", os.getenv("ENVIRONMENT", "")).strip().lower()
        if environment not in ALLOWED_DEMO_ENVIRONMENTS | {"production"}:
            raise RuntimeError(
                "SAHAYA_ENV must be explicitly set to development, local, test, or production"
            )
        default_origins = (
            "http://localhost:5173,http://127.0.0.1:5173"
            if environment in {"development", "local", "test"}
            else ""
        )
        configured_cors_origins = os.getenv("SAHAYA_CORS_ORIGINS", os.getenv("CORS_ORIGINS", default_origins))
        cors_origins = tuple(
            origin.strip()
            for origin in configured_cors_origins.split(",")
            if origin.strip()
        )
        jwt_secret_key = os.getenv("SAHAYA_JWT_SECRET_KEY", "").strip()
        otp_secret_encryption_key = os.getenv(
            "SAHAYA_OTP_SECRET_ENCRYPTION_KEY", ""
        ).strip()
        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        # Synthetic application data is opt-in. Test runs may opt in by using
        # SAHAYA_ENV=test; local development never exposes seeded demo rows by
        # default. Authentication accounts are unaffected by this flag.
        demo_data_enabled = (
            os.getenv("SAHAYA_INCLUDE_DEMO_DATA", "").strip().lower()
            in {"1", "true", "yes"}
            and environment in ALLOWED_DEMO_ENVIRONMENTS
        )
        upload_directory = os.getenv("SAHAYA_UPLOAD_DIRECTORY", "").strip() or str(backend_root / "uploads")
        upload_max_bytes = min(
            int(os.getenv("SAHAYA_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))),
            10 * 1024 * 1024,
        )
        if environment == "production":
            if not jwt_secret_key:
                raise RuntimeError("SAHAYA_JWT_SECRET_KEY is required in production")
            if not os.getenv("SAHAYA_DATABASE_URL", "").strip():
                raise RuntimeError("SAHAYA_DATABASE_URL is required in production")
            if not os.getenv("SAHAYA_CORS_ORIGINS", "").strip():
                raise RuntimeError("SAHAYA_CORS_ORIGINS is required in production")
            if os.getenv("SAHAYA_REFRESH_COOKIE_SECURE", "true").strip().lower() not in {"1", "true", "yes"}:
                raise RuntimeError("SAHAYA_REFRESH_COOKIE_SECURE must be true in production")
            if os.getenv("SAHAYA_JWT_ALGORITHM", "HS256").strip() != "HS256":
                raise RuntimeError("Only HS256 is allowed for the configured JWT algorithm")
        if not jwt_secret_key:
            jwt_secret_key = _EPHEMERAL_DEVELOPMENT_JWT_SECRET
        if not otp_secret_encryption_key:
            otp_secret_encryption_key = jwt_secret_key
        database_url = os.getenv("SAHAYA_DATABASE_URL", os.getenv("DATABASE_URL", "")).strip()
        if not database_url:
            database_url = f"sqlite:///{backend_root / 'sahaya.db'}"
        return cls(
            environment=environment,
            database_url=database_url,
            cors_origins=cors_origins,
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=os.getenv("SAHAYA_JWT_ALGORITHM", "HS256").strip(),
            jwt_issuer=os.getenv("SAHAYA_JWT_ISSUER", "sahaya-api").strip(),
            jwt_audience=os.getenv("SAHAYA_JWT_AUDIENCE", "sahaya-web").strip(),
            access_token_minutes=int(os.getenv("SAHAYA_ACCESS_TOKEN_MINUTES", "15")),
            refresh_token_days=int(os.getenv("SAHAYA_REFRESH_TOKEN_DAYS", "7")),
            refresh_cookie_secure=os.getenv(
                "SAHAYA_REFRESH_COOKIE_SECURE",
                "true" if environment == "production" else "false",
            ).strip().lower()
            in {"1", "true", "yes"},
            otp_secret_encryption_key=otp_secret_encryption_key,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            demo_data_enabled=demo_data_enabled,
            upload_directory=upload_directory,
            upload_max_bytes=upload_max_bytes,
            otp_totp_interval_seconds=int(
                os.getenv("SAHAYA_OTP_TOTP_INTERVAL_SECONDS", "30")
            ),
            otp_totp_digits=int(os.getenv("SAHAYA_OTP_TOTP_DIGITS", "6")),
            otp_totp_valid_window=int(
                os.getenv("SAHAYA_OTP_TOTP_VALID_WINDOW", "1")
            ),
            otp_expiry_minutes=int(os.getenv("SAHAYA_OTP_EXPIRY_MINUTES", "5")),
            otp_start_cooldown_seconds=int(
                os.getenv("SAHAYA_OTP_START_COOLDOWN_SECONDS", "30")
            ),
            otp_resend_cooldown_seconds=int(
                os.getenv("SAHAYA_OTP_RESEND_COOLDOWN_SECONDS", "60")
            ),
            otp_window_max_requests=int(
                os.getenv("SAHAYA_OTP_WINDOW_MAX_REQUESTS", "5")
            ),
            otp_max_verify_attempts=int(
                os.getenv("SAHAYA_OTP_MAX_VERIFY_ATTEMPTS", "5")
            ),
        )

    def require_demo_seed_allowed(self) -> None:
        if self.environment not in ALLOWED_DEMO_ENVIRONMENTS:
            allowed = ", ".join(sorted(ALLOWED_DEMO_ENVIRONMENTS))
            raise DemoSeedEnvironmentError(
                "Demo seeding is blocked outside local/development/test "
                f"environments (SAHAYA_ENV={self.environment!r}). Allowed: {allowed}."
            )

    def reject_obvious_production_database(self) -> None:
        """Second safety check for a production-looking database identifier."""
        normalized = self.database_url.casefold()
        production_markers = (
            "sahaya_production",
            "sahaya-prod",
            "sahaya.prod",
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
