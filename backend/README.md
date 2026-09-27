# SAATHI backend

FastAPI/SQLAlchemy backend with real authentication, structured errors, restricted CORS, controlled SQLite demo personas, and explicit demo-data isolation.

## Run locally

```bash
cd backend
python3 -m pip install -r requirements.txt
SAATHI_ENV=development \
SAATHI_JWT_SECRET_KEY='replace-with-a-long-random-development-secret' \
python3 -m uvicorn app.main:app --reload
```

Health endpoints:

```text
GET /health
GET /api/v1/health
```

## Authentication

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/me
POST /api/v1/auth/otp/start
POST /api/v1/auth/otp/verify
POST /api/v1/auth/otp/resend
POST /api/v1/profile
GET  /api/v1/profile
PATCH /api/v1/profile
```

The backend uses short-lived JWT access tokens and a rotating refresh cookie. Demo users authenticate through the same `/api/v1/auth/login` route as all other accounts.

## Demo personas

```bash
SAATHI_ENV=development python3 -m app.demo.seed_demo
```

Reset:

```bash
SAATHI_ENV=development python3 -m app.demo.reset_demo
```

Unique fictional credentials and the complete role-specific data map are documented in `docs/DEMO_ACCOUNTS.md`.

The seed is idempotent, environment-gated, fully marked with `is_demo=true`, and has no public HTTP endpoint. Demo status is provenance only and is never an authentication or administrator bypass.

## Test

```bash
SAATHI_ENV=test SAATHI_DATABASE_URL='sqlite:///:memory:' python3 -m pytest -q
```
