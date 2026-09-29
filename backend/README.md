# SAHAYA backend

FastAPI/SQLAlchemy backend with real authentication, structured errors, restricted CORS, controlled SQLite demo personas, and explicit demo-data isolation.

## Run locally

```bash
cd backend
python3 -m pip install -r requirements.txt
SAHAYA_ENV=development \
SAHAYA_JWT_SECRET_KEY='replace-with-a-long-random-development-secret' \
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

## Local test authentication

The five development role-login accounts are seeded independently from
synthetic application records:

```bash
SAHAYA_ENV=development python3 -m app.demo.seed_test_auth
```

This creates only authentication/profile/scope records. It does not create
cases, check-ins, documents, support requests, assignments, notifications, or
legal records.

## Demo personas

```bash
SAHAYA_ENV=development python3 -m app.demo.seed_demo
```

Reset:

```bash
SAHAYA_ENV=development python3 -m app.demo.reset_demo
```

Unique fictional credentials and the complete role-specific data map are documented in `docs/DEMO_ACCOUNTS.md`.

The full seed is idempotent, environment-gated, fully marked with
`is_demo=true`, and has no public HTTP endpoint. It is an explicit test fixture;
normal runtime APIs exclude these rows unless `SAHAYA_INCLUDE_DEMO_DATA=true`
is set in a non-production test/development process.

To remove only synthetic application records while preserving local test-login
accounts:

```bash
SAHAYA_ENV=development python3 -m app.demo.reset_demo_application
```

## Test

```bash
SAHAYA_ENV=test SAHAYA_DATABASE_URL='sqlite:///:memory:' python3 -m pytest -q
```
