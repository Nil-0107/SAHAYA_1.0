# SAHAYA Final Architecture

**Status:** Final architecture definition  
**Scope:** MVP modular monolith  
**Implementation rule:** This document defines boundaries and contracts only. Product functionality must not be implemented until the corresponding bounded phase.

## 1. Architecture goals

SAHAYA will be implemented as one frontend, one FastAPI backend, one relational database, and local file storage:

```text
React
  → Axios
  → FastAPI
  → Services
  → SQLAlchemy / SQLite
  → Local ML / Gemini / Twilio adapters
```

The system must provide:

- Privacy-first account, profile, case, check-in, and support workflows.
- Backend-enforced authentication, ownership, role, and scope authorization.
- Account-mobile verification through server-side PyOTP and Twilio SMS.
- A local scikit-learn emotion classifier with unknown semantic labels preserved.
- Server-side Gemini support with safe fallback behavior.
- Deterministic, explainable priority based only on verified backend facts.
- Human support, assignment, notification, and audit workflows.
- Controlled synthetic demo personas that never bypass authentication or enter production databases.

## 2. Explicit non-goals

The MVP will not introduce:

- Microservices.
- Kafka or any message broker.
- Redis or another cache/broker.
- Kubernetes.
- A message queue.
- A separate ML service.
- A separate Gemini service.
- A separate notification service.
- A separate auth service.
- Real-time emergency dispatch.
- Automatic police or emergency-service contact.
- A clinical diagnosis engine.
- A legal decision engine.
- Fabricated case verification or administrative analytics.

These capabilities may be reconsidered only after measured production requirements justify them. They are not part of the current architecture.

---

# 3. System context

```text
┌──────────────────────────────────────────────────────────────┐
│ Browser                                                       │
│                                                              │
│ React + TypeScript                                           │
│ ├── React Router                                             │
│ ├── Tailwind CSS                                             │
│ ├── lucide-react                                              │
│ ├── AuthContext and feature hooks                            │
│ └── Typed Axios service clients                              │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS / same-origin deployment
                            │ JSON; multipart only for case upload
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI application                                           │
│                                                              │
│ API routes and Pydantic schemas                              │
│ ├── Authentication and authorization dependencies            │
│ ├── Domain services                                          │
│ ├── SQLAlchemy session and models                            │
│ ├── Audit service                                            │
│ └── Explicit error mapping                                   │
│                                                              │
│ Services call only approved adapters:                        │
│ ├── SQLite through SQLAlchemy                                │
│ ├── Local filesystem for case documents                      │
│ ├── Trusted local Joblib artifacts                           │
│ ├── Google Gemini through google-genai                       │
│ └── Twilio SMS through a server-only Python SDK adapter     │
└──────────────────────────────────────────────────────────────┘
```

There is one deployable backend application. Integrations are in-process adapters, not independently deployed services.

---

# 4. Frontend architecture

## 4.1 Technology

The frontend uses only the approved stack:

- React.
- Vite.
- TypeScript.
- Tailwind CSS.
- React Router.
- Axios.
- `lucide-react`.

Vitest and React Testing Library will be added when frontend testing is implemented. No additional state-management or data-fetching framework is required for the MVP.

## 4.2 Mandatory frontend structure

```text
frontend/
├── public/
│   └── assets/
└── src/
    ├── assets/
    ├── components/
    │   ├── common/
    │   ├── forms/
    │   ├── navigation/
    │   ├── cards/
    │   ├── modals/
    │   ├── feedback/
    │   └── charts/
    ├── layouts/
    │   ├── PublicLayout.tsx
    │   ├── AuthLayout.tsx
    │   ├── VictimLayout.tsx
    │   ├── CounsellorLayout.tsx
    │   ├── DistrictOfficerLayout.tsx
    │   └── AdminLayout.tsx
    ├── pages/
    │   ├── public/
    │   ├── auth/
    │   ├── victim/
    │   ├── counsellor/
    │   ├── district-officer/
    │   └── admin/
    ├── features/
    │   ├── auth/
    │   ├── profile/
    │   ├── checkins/
    │   ├── ai/
    │   ├── cases/
    │   ├── support/
    │   ├── notifications/
    │   └── priority/
    ├── hooks/
    ├── services/
    │   ├── api.ts
    │   ├── authApi.ts
    │   ├── profileApi.ts
    │   ├── checkinApi.ts
    │   ├── aiApi.ts
    │   ├── caseApi.ts
    │   ├── supportApi.ts
    │   └── notificationApi.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── routes/
    │   ├── AppRouter.tsx
    │   ├── ProtectedRoute.tsx
    │   └── RoleRoute.tsx
    ├── types/
    ├── utils/
    ├── config/
    ├── App.tsx
    ├── main.tsx
    └── index.css
```

## 4.3 Frontend layers

### Presentation

- `pages/` defines route-level screens.
- `layouts/` defines public, authentication, and role-specific shells.
- `components/` contains reusable visual and behavioral primitives.
- `features/` contains domain-specific UI composition and hooks.

Pages must not construct raw HTTP requests.

### Domain state

- `AuthContext` owns the current session bootstrap and current-user state.
- Feature hooks own loading, success, empty, and error state.
- Domain data is fetched through typed service clients.
- No sensitive profile, case, or check-in content is written to localStorage, sessionStorage, URLs, analytics events, or frontend source.
- Access tokens, if used, are held in memory only and are not persisted to browser storage.

### Routing

React Router owns navigation and UX-level route protection:

- `PublicLayout`: landing and public routes.
- `AuthLayout`: login, signup, role selection, OTP, and profile setup.
- `VictimLayout`: victim routes.
- `CounsellorLayout`: counsellor routes.
- `DistrictOfficerLayout`: district routes.
- `AdminLayout`: administrator routes.

`ProtectedRoute` and `RoleRoute` improve user experience only. They are not security boundaries. Every protected API call must independently authenticate and authorize on FastAPI.

## 4.4 Frontend route groups

### Public and authentication

- `/`
- `/login`
- `/signup`
- `/signup/role`
- `/signup/otp`
- `/profile/setup`
- `/forbidden`
- `*` not-found route

The exact login/signup role order must follow the final approved UX. A role card never grants backend authority.

### Victim

- `/victim`
- `/victim/check-ins`
- `/victim/ai`
- `/victim/case`
- `/victim/progress`
- `/victim/support`
- `/victim/legal-information`
- `/victim/notifications`

### Counsellor

- `/counsellor`
- `/counsellor/requests`
- `/counsellor/cases/:caseId`
- `/counsellor/support-actions`
- `/counsellor/notifications`

### District officer

- `/district-officer`
- `/district-officer/requests`
- `/district-officer/cases/:caseId`
- `/district-officer/assignments`
- `/district-officer/documents`
- `/district-officer/notifications`

### Administrator

- `/admin`
- `/admin/queue`
- `/admin/cases/:caseId`
- `/admin/audit`
- `/admin/model-health`

The default administrator experience is aggregate-only. Individual sensitive details require a separate authorized case view.

## 4.5 Axios architecture

`src/services/api.ts` is the single Axios instance and sole source of API base configuration.

Responsibilities:

- Base URL configuration.
- JSON request/response handling.
- Access-token header injection when an in-memory access token exists.
- One controlled 401/session-expiry path.
- Human-readable API error normalization.
- No automatic logging of request bodies, check-in text, case data, tokens, or provider responses.

Feature clients own endpoint methods and response types:

- `authApi`
- `profileApi`
- `checkinApi`
- `aiApi`
- `caseApi`
- `supportApi`
- `notificationApi`

Case upload uses an explicit multipart client rather than forcing JSON headers onto every request.

## 4.6 Frontend state and errors

Every asynchronous feature must distinguish:

- Loading.
- Success.
- Empty.
- Recoverable error.
- Unauthorized/forbidden.
- Service unavailable/not configured.

The frontend must display the backend's safe human-readable message without exposing stack traces or internal prompts.

---

# 5. Backend architecture

## 5.1 Technology

The backend uses only the approved stack:

- Python.
- FastAPI.
- SQLAlchemy.
- Pydantic.
- SQLite for MVP.
- `joblib` and `scikit-learn` for local inference.
- `google-genai` for server-side Gemini access.
- Local filesystem storage for MVP case documents.
- Pytest and FastAPI TestClient for backend tests.

PostgreSQL is a later production migration path, not part of the MVP runtime topology.

## 5.2 Mandatory backend structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── dependencies.py
│   │   └── logging.py
│   ├── db/
│   │   ├── database.py
│   │   ├── base.py
│   │   └── init_db.py
│   ├── models/
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── case.py
│   │   ├── case_document.py
│   │   ├── checkin.py
│   │   ├── support_request.py
│   │   ├── case_assignment.py
│   │   ├── support_action.py
│   │   ├── notification.py
│   │   ├── otp_verification.py
│   │   ├── ai_conversation.py
│   │   ├── ai_message.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── case.py
│   │   ├── checkin.py
│   │   ├── support.py
│   │   ├── notification.py
│   │   ├── ai.py
│   │   └── common.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── profile.py
│   │       ├── checkins.py
│   │       ├── ai.py
│   │       ├── cases.py
│   │       ├── support.py
│   │       ├── notifications.py
│   │       └── admin.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   ├── profile_service.py
│   │   ├── checkin_service.py
│   │   ├── ml_service.py
│   │   ├── gemini_service.py
│   │   ├── case_service.py
│   │   ├── support_service.py
│   │   ├── notification_service.py
│   │   ├── priority_service.py
│   │   └── audit_service.py
│   ├── integrations/
│   │   ├── twilio_sms.py
│   │   └── gemini.py
│   ├── ml/
│   │   ├── loader.py
│   │   ├── inference.py
│   │   └── artifacts/
│   ├── demo/
│   │   ├── seed_demo.py
│   │   ├── personas.py
│   │   └── reset_demo.py
│   └── utils/
│       ├── validators.py
│       └── files.py
├── tests/
├── uploads/
├── .env.example
├── requirements.txt
└── README.md
```

## 5.3 Backend layer rules

```text
API route
  → Pydantic request/response schema
  → authenticated/authorized dependency
  → domain service
  → SQLAlchemy model/session or approved integration adapter
```

Rules:

1. API routes validate transport input and map HTTP status codes.
2. API routes do not contain business rules or direct provider calls.
3. Services own business workflows and transaction boundaries.
4. Services may use SQLAlchemy directly; no additional repository framework is required for MVP.
5. Integrations are called only by their owning service.
6. Models contain persistence definitions, not business workflows.
7. Pydantic schemas contain transport contracts, not authorization decisions.
8. Demo modules are never imported by application startup or API routes.
9. Gemini, Twilio, ML, and priority modules remain independent of one another.

---

# 6. Shared backend foundations

## 6.1 Configuration

`app/core/config.py` is the only source of server configuration.

Required configuration groups:

- Environment.
- Database URL.
- JWT signing key, algorithm, access lifetime, refresh lifetime.
- Allowed CORS origins.
- Upload directory and maximum upload size.
- Twilio account/authentication and SMS destination settings.
- Server-only TOTP secret-encryption key.

OTP/Twilio environment variables are read only by the backend: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, optional `TWILIO_VERIFY_SERVICE_SID` placeholder, optional `TWILIO_API_KEY_SID`/`TWILIO_API_KEY_SECRET`, and one of `TWILIO_MESSAGING_SERVICE_SID` or `TWILIO_FROM_NUMBER`. The selected implementation uses PyOTP with Twilio Programmable Messaging, so the Verify service SID is not consumed by the current TOTP service. `SAHAYA_OTP_SECRET_ENCRYPTION_KEY` protects TOTP secrets at rest. None of these values use a `VITE_` prefix.
- Gemini API key and model.
- ML artifact paths and expected model metadata.
- Logging level and redaction policy.

Rules:

- Secrets are read only on the server.
- No secret is prefixed with `VITE_`.
- Production configuration fails fast if required secrets/settings are missing.
- Local/test/demo configuration cannot silently fall back to production.
- Demo seed additionally verifies that its active database session matches the explicitly approved local/test database.

## 6.2 Authentication strategy

The architecture uses:

- A short-lived signed JWT access token returned by login/refresh and held in frontend memory.
- A rotating refresh token stored in a `Secure`, `HttpOnly`, `SameSite` cookie.
- Only a hash of the refresh token stored server-side.
- Refresh-token rotation and reuse detection.
- Logout revokes the server-side refresh session.
- No access or refresh token in localStorage/sessionStorage.
- No sensitive profile, case, support, or check-in data in JWT claims.

The access token contains only minimal identity and authorization metadata such as user ID, role, token ID, issued time, and expiry. It does not contain sensitive case/profile content.

## 6.3 Authorization

Authorization is enforced in FastAPI dependencies and domain services.

Authorization inputs:

- Authenticated user ID.
- User role.
- Explicit state/national/district scope.
- Case ownership.
- Active case/support assignment.
- Requested operation.
- Resource ownership and state.

Roles:

- Victim/User: own profile, cases, check-ins, support requests, and notifications.
- Counsellor/Psychologist: assigned well-being records and authorized support context.
- District Officer: cases and services within assigned district scope.
- State/National Administrator: aggregate monitoring by default and explicitly authorized case/audit access.

A public signup request may create only a Victim/User account. Privileged roles require a future controlled invitation/provisioning path. A UI role selection is never sufficient to create a counsellor, district officer, or administrator.

## 6.4 Database

SQLAlchemy models are split by domain under `app/models/`.

MVP persistence entities:

- `users`
- `profiles`
- `otp_verifications`
- `cases`
- `case_documents`
- `checkins`
- `support_requests`
- `case_assignments`
- `support_actions`
- `notifications`
- `ai_conversations`
- `ai_messages`
- `audit_logs`
- `model_registry`

Authorization-scope data must be represented explicitly rather than inferred from free-text district names.

Database rules:

- Migrations are the only supported schema-change mechanism.
- `create_all()` is not a migration strategy.
- Foreign keys and uniqueness constraints are enforced.
- Sensitive text is never written to logs.
- Case-document storage paths are never returned by API serializers.
- Administrator serializers default to aggregates and exclude raw sensitive content.
- Audit records are append-only at the service/API boundary.

SQLite is the MVP database. PostgreSQL migration work is deferred until the MVP is functionally complete.

## 6.5 Error contract

API errors use a stable Pydantic error shape with:

- Machine-readable code.
- Human-readable message.
- Optional request ID.
- Optional field-level validation details.

Required HTTP behavior:

| Condition | Status |
|---|---:|
| Invalid request/upload | 400 |
| Missing/invalid authentication | 401 |
| Authenticated but unauthorized | 403 |
| Resource not found without disclosure | 404 |
| File too large | 413 |
| Rate limited | 429 |
| Database unavailable | 503 |
| ML unavailable | 503 |
| Gemini unavailable | safe graceful response/fallback |
| Unexpected server error | 500 with no stack trace |

---

# 7. Domain module architecture

## 7.1 Auth module

### Files

- API: `app/api/v1/auth.py`
- Schemas: `app/schemas/auth.py`, `app/schemas/user.py`
- Service: `app/services/auth_service.py`
- OTP service: `app/services/otp_service.py`
- Security: `app/core/security.py`
- Dependencies: `app/core/dependencies.py`
- Twilio adapter: `app/integrations/twilio_sms.py`
- Secret encryption: `app/core/secret_cipher.py`
- Phone normalization: `app/core/phones.py`

### Responsibilities

- Signup.
- Login.
- Logout.
- Access-token refresh.
- Current user.
- Password hashing and verification.
- JWT/session lifecycle.
- Account-mobile OTP start/resend/verify.
- Server-side PyOTP code generation and verification.
- Twilio SMS delivery without browser-side provider access.
- Authentication and verification audit events.
- Login/OTP rate limiting.

### Required API

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/me

POST /api/v1/auth/otp/start
POST /api/v1/auth/otp/verify
POST /api/v1/auth/otp/resend
```

### OTP state machine

```text
PENDING → SENT → VERIFYING → VERIFIED
                  ↘ EXPIRED
                  ↘ INVALID
                  ↘ PROVIDER_ERROR
                  ↘ RATE_LIMITED
```

A verified OTP transaction is consumed and cannot be replayed. The account mobile is the only OTP target. Emergency contact is a separate profile concept.

---

## 7.2 Profiles module

### Files

- API: `app/api/v1/profile.py`
- Schemas: `app/schemas/profile.py`
- Model: `app/models/profile.py`
- Service: `app/services/profile_service.py`

### Responsibilities

- One-time profile setup.
- Explicit profile update.
- Preferred language and district.
- Consent timestamp.
- Optional emergency contact and safe contact method.
- Profile completion state.
- Ownership enforcement.
- Profile-change audit events.

### Required API

```text
POST  /api/v1/profile
PATCH /api/v1/profile
GET   /api/v1/profile
```

The setup flow must visibly and logically distinguish account mobile from emergency contact.

---

## 7.3 Demo personas module

### Files

- `app/demo/personas.py`
- `app/demo/seed_demo.py`
- `app/demo/reset_demo.py`
- Scripts: `scripts/seed-demo.sh`, `scripts/reset-demo.sh`

### Responsibilities

- Define clearly fictional identities.
- Seed all supported roles.
- Create realistic relationships among users, cases, check-ins, support requests, notifications, assignments, and audit records.
- Mark every seeded row `is_demo=true`.
- Reconcile stable `demo_key` values idempotently.
- Refuse production/staging environments.
- Refuse to modify non-demo natural keys.
- Reset only the managed demo namespace in a transaction.
- Never expose seed/reset through HTTP.
- Never create an authentication bypass.

Demo users, once real authentication exists, log in through the same auth service as all other users.

---

## 7.4 Cases module

### Files

- API: `app/api/v1/cases.py`
- Schemas: `app/schemas/case.py`
- Models: `app/models/case.py`, `app/models/case_document.py`
- Service: `app/services/case_service.py`
- File utilities: `app/utils/files.py`

### Responsibilities

- Own-case listing.
- Case creation/ingestion.
- Authorized case details.
- Document metadata and storage.
- Ownership and assignment authorization.
- Case state/timeline/authorized updates.
- Safe case serializers.
- Case-change audit events.

### Required API

```text
GET  /api/v1/cases/me
POST /api/v1/cases/upload
GET  /api/v1/cases/{id}
```

### Upload boundary

- PDF, JPG/JPEG, PNG only.
- Maximum 10 MB.
- Server-generated random storage name.
- Extension, MIME, size, and file-signature validation.
- Storage outside the frontend.
- Database stores metadata and internal path.
- Internal storage path never returned to the browser.
- No executable content.

CNR lookup, voice statements, and IVRS remain explicitly unavailable until separately approved and implemented.

---

## 7.5 Check-ins module

### Files

- API: `app/api/v1/checkins.py`
- Schemas: `app/schemas/checkin.py`
- Model: `app/models/checkin.py`
- Service: `app/services/checkin_service.py`
- ML adapter: `app/services/ml_service.py`, `app/ml/`

### Responsibilities

- Authenticate the user.
- Validate check-in text.
- Authorize optional case linkage.
- Store the check-in securely.
- Invoke local ML inference.
- Persist class ID and confidence.
- Keep semantic label `null` unless verified metadata is available.
- Return a supportive, non-diagnostic response.
- Record access/audit events without logging raw text.

### Required API

```text
POST /api/v1/checkins
GET  /api/v1/checkins/me
```

### Module flow

```text
Check-in API
  → CheckinService
  → save authorized check-in
  → WellbeingService
  → TF-IDF + Logistic Regression
  → save numeric class/confidence
  → safe response
```

---

## 7.6 Support module

### Files

- API: `app/api/v1/support.py`
- Schemas: `app/schemas/support.py`
- Models:
  - `support_request.py`
  - `case_assignment.py`
  - `support_action.py`
- Service: `app/services/support_service.py`

### Responsibilities

- Human well-being support requests.
- Legal-assistance requests.
- Protection/relocation requests.
- Assignment creation and history.
- Authorized counsellor/district queues.
- Support status and actions.
- Ownership, role, and scope checks.
- Support-change audit events.

### Required API

```text
POST /api/v1/support-requests
GET  /api/v1/support-requests/me
GET  /api/v1/support-requests/assigned
GET  /api/v1/support-requests/{id}
POST /api/v1/support-requests/{id}/actions
POST /api/v1/case-assignments
GET  /api/v1/case-assignments/{caseId}
```

A support or protection request does not claim that police, emergency services, lawyers, courts, or other external parties were contacted.

---

## 7.7 Notifications module

### Files

- API: `app/api/v1/notifications.py`
- Schemas: `app/schemas/notification.py`
- Model: `app/models/notification.py`
- Service: `app/services/notification_service.py`

### Responsibilities

- Create notifications transactionally from domain events.
- List only the authenticated recipient's notifications.
- Mark only owned notifications as read.
- Support unread counts.
- Avoid sensitive content in notification previews.
- Generate no external SMS/email claim unless a real provider is configured.

### Required API

```text
GET  /api/v1/notifications
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all
```

For MVP, notification creation is an in-process database write in the same application. No queue, Kafka, Redis, or worker service is introduced.

---

## 7.8 AI module

### Files

- API: `app/api/v1/ai.py`
- Schemas: `app/schemas/ai.py`
- Models: `ai_conversation.py`, `ai_message.py`
- Service: `app/services/gemini_service.py`
- Adapter: `app/integrations/gemini.py`

### Responsibilities

- Server-side Gemini support chat.
- Optional case-document extraction.
- Optional authorized support summaries.
- Conversation ownership and persistence.
- Safety-policy enforcement.
- Immediate-danger flow selection.
- Graceful Gemini unavailability fallback.

### Required API

```text
POST /api/v1/ai/chat
POST /api/v1/ai/case-extract
```

### Safety boundaries

AI must not:

- Diagnose a mental-health condition.
- Provide definitive legal conclusions.
- Claim case verification.
- Claim any person or service was contacted.
- Reveal prompts, keys, database internals, scores, or model details.
- Calculate official priority.
- Replace human professional review.

Gemini failure returns a safe fallback such as `AI support temporarily unavailable`. Local CRUD and local ML remain independently usable.

---

## 7.9 ML module

### Files

- Compatibility service: `app/services/ml_service.py`
- Loader: `app/ml/loader.py`
- Inference: `app/ml/inference.py`
- Artifacts: `app/ml/artifacts/`
- Model registry: `app/models/model_registry.py` when database work is implemented

### Responsibilities

- Validate required artifacts at application startup.
- Load each trusted artifact once per application process.
- Validate text before inference.
- Run TF-IDF transformation.
- Run logistic-regression `predict_proba`.
- Return numeric class ID and confidence.
- Return a semantic label only from verified training metadata.
- Record artifact checksum/version/runtime metadata.
- Fail clearly with a safe 503 when unavailable.

### Artifact contract

- Vectorizer: `TfidfVectorizer(max_features=5000)`.
- Model: six classes `[0,1,2,3,4,5]`.
- Features/vocabulary: 5,000.
- No semantic class names are currently verified.

### Risk boundary

`RiskEngine` is a separate interface. Its MVP implementation returns `NOT_CONFIGURED`. Emotion probabilities must never be converted into a distress, diagnosis, or safety score.

---

## 7.10 Priority module

### Files

- Admin API: `app/api/v1/admin.py`
- Schemas: `app/schemas/support.py` or a dedicated priority schema added during implementation
- Service: `app/services/priority_service.py`
- Model registry/health: `app/models/model_registry.py` when implemented

### Responsibilities

- Deterministic priority calculation.
- Verified-fact inputs only.
- Human-readable reason generation.
- Authorized administrator queue.
- Explicit recalculation endpoint.
- No raw internal model or score details exposed to users.

### Inputs

```text
verified high-priority category       +70
open protection request               +20
explicit human support request        +15
verified well-being review flag       +10
maximum                               100
```

Verified categories are limited to the approved policy:

```text
RAPE_OR_GANG_RAPE
MURDER_GRIEVOUS_HURT_ARSON
WITNESS_INTIMIDATION_OR_THREATS
CASTE_BASED_VIOLENCE_FAMILY_AFFECTED
```

The service is pure and deterministic. It does not call Gemini or interpret emotion-model output.

### Required API

```text
GET  /api/v1/admin/queue
GET  /api/v1/admin/cases/{id}
POST /api/v1/admin/cases/{id}/priority-recalculate
```

---

## 7.11 Audit module

### Files

- Model: `app/models/audit_log.py`
- Service: `app/services/audit_service.py`
- API exposure: read-only authorized admin/audit routes

### Responsibilities

Record:

- Signup.
- Login.
- Logout.
- Failed authentication without recording passwords.
- Account verification.
- Profile changes.
- Case access/changes/uploads.
- Assignment changes.
- Support changes/actions.
- Privileged access.
- Administrator changes.
- Model configuration changes.
- Priority recalculation.

Audit rules:

- Append-only through application services.
- No raw passwords, OTPs, JWTs, refresh tokens, provider keys, or unnecessary check-in text.
- Metadata is structured and minimized.
- Audit failures for security-sensitive operations are surfaced and handled according to the operation's consistency requirements.
- Administrators see audit data only through authorized routes.

---

# 8. API architecture

## 8.1 Versioning

All product endpoints use:

```text
/api/v1
```

Health remains:

```text
GET /health
```

## 8.2 Router composition

`app/api/v1/router.py` includes only implemented, tested routers.

Feature routers are not attached merely because their files exist. A router becomes attached only when its schemas, service, authorization, audit behavior, and tests are implemented.

## 8.3 Endpoint groups

### Auth and profile

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/me
POST /api/v1/auth/otp/start
POST /api/v1/auth/otp/verify
POST /api/v1/auth/otp/resend
POST /api/v1/profile
PATCH /api/v1/profile
GET  /api/v1/profile
```

### Cases and check-ins

```text
GET  /api/v1/cases/me
POST /api/v1/cases/upload
GET  /api/v1/cases/{id}
POST /api/v1/checkins
GET  /api/v1/checkins/me
```

### AI and support

```text
POST /api/v1/ai/chat
POST /api/v1/ai/case-extract
POST /api/v1/support-requests
GET  /api/v1/support-requests/me
GET  /api/v1/support-requests/assigned
GET  /api/v1/support-requests/{id}
POST /api/v1/support-requests/{id}/actions
```

### Administration and priority

```text
GET  /api/v1/admin/queue
GET  /api/v1/admin/cases/{id}
POST /api/v1/admin/cases/{id}/priority-recalculate
GET  /api/v1/admin/audit
```

### Notifications and dashboards

```text
GET  /api/v1/notifications
POST /api/v1/notifications/{id}/read
GET  /api/v1/dashboard/victim
GET  /api/v1/dashboard/counsellor
GET  /api/v1/dashboard/district
GET  /api/v1/dashboard/admin
```

Dashboards use backend aggregation queries. The frontend does not calculate privileged analytics from incomplete data.

---

# 9. Request flows

## 9.1 Signup and account verification

```text
React Signup
  → Axios authApi.signup
  → FastAPI auth route
  → Pydantic E.164 validation
  → AuthService creates unverified Victim/User
  → OtpService generates a random TOTP secret
  → Secret is authenticated-encrypted at rest
  → PyOTP generates the six-digit code in backend memory
  → Twilio server adapter sends the code by SMS
  → Browser receives only a safe success response
  → User enters the six-digit code
  → React sends phone and code to the backend verify endpoint
  → OtpService decrypts the TOTP secret and verifies with PyOTP
  → OtpService consumes the transaction and erases its secret
  → User phone marked verified
  → AuditService records verification without the code or secret
  → Frontend continues to one-time profile setup
```

Neither the browser nor Twilio can activate the account without the backend-owned transaction and PyOTP verification. Twilio credentials are never returned to the browser.

## 9.2 Login

```text
React Login
  → Axios authApi.login
  → FastAPI login route
  → rate-limit/password policy
  → AuthService verifies scrypt hash
  → short-lived access JWT returned
  → rotating refresh token stored in HttpOnly cookie
  → audit login
  → AuthContext loads /me
  → router redirects to complete dashboard or profile setup
```

## 9.3 Check-in and ML

```text
React Check-in
  → Axios checkinApi.create
  → authenticated Checkin route
  → CheckinService validates ownership/case access
  → transaction stores check-in
  → WellbeingService runs trusted local artifacts
  → numeric class/confidence saved
  → optional RiskEngine returns NOT_CONFIGURED
  → safe non-diagnostic response
```

## 9.4 Human support and assignment

```text
React Support request
  → Axios supportApi.create
  → SupportService validates victim/case ownership
  → support request saved
  → deterministic priority calculated from verified facts
  → assignment created only by authorized role/scope
  → NotificationService writes recipient notifications
  → AuditService records request/assignment
```

## 9.5 Case upload

```text
React multipart upload
  → Axios caseApi.upload
  → authenticated case route
  → CaseService verifies ownership/role
  → streaming validation
  → random server filename
  → local file storage
  → case_documents metadata saved
  → audit event
  → safe response without storage path
```

## 9.6 Gemini support

```text
React AI chat
  → Axios aiApi.chat
  → authenticated AI route
  → conversation ownership checked
  → GeminiService applies safety policy
  → google-genai adapter called server-side
  → response validated/sanitized
  → AI messages persisted
  → safe response returned
```

---

# 10. Storage architecture

## 10.1 Database

SQLite stores:

- Users and authorization data.
- Profiles and consent.
- OTP state.
- Cases and case metadata.
- Document metadata.
- Check-ins and numeric ML output.
- Support requests, assignments, and actions.
- Notifications.
- AI conversation/message metadata.
- Audit records.
- Model registry metadata.

## 10.2 Filesystem

The local filesystem stores uploaded case documents outside the frontend.

Rules:

- Random server-generated names.
- Metadata in SQLite.
- No executable uploads.
- No raw path in API responses.
- Directory excluded from version control.
- Upload lifecycle and access are controlled by case authorization.

Object storage can be evaluated after the MVP; it is not part of the current architecture.

---

# 11. Security architecture

## 11.1 Backend security

- Authentication required for all protected endpoints.
- Role and scope checks in dependencies/services.
- Ownership checks for victim resources.
- Assignment checks for counsellor/district resources.
- Aggregate-only administrator defaults.
- IDOR tests for every resource route.
- Rate limiting for login, signup, OTP, refresh, and AI routes.
- Secure upload streaming and content-signature validation.
- Pydantic validation at every boundary.
- Parameterized SQLAlchemy queries.
- No raw sensitive values in logs.
- No internal error details in responses.
- Restricted CORS or same-origin reverse proxy.
- Production security headers and TLS termination.

## 11.2 Frontend security

- React escaping; no unsafe HTML injection.
- No sensitive browser storage.
- No provider secrets or server keys.
- No client-only OTP verification.
- No client-side priority calculation.
- No reliance on hidden buttons/routes for security.
- Human-readable errors without stack traces.

## 11.3 Demo isolation

- Demo commands only.
- Explicit local/development/test environment.
- Dedicated or verifiably bound demo database.
- Every row marked `is_demo=true`.
- Stable seed namespace.
- Refusal to overwrite non-demo records.
- No public seed/reset route.
- No demo auth bypass.

---

# 12. Reliability and failure behavior

## 12.1 Database

- Transactions per write workflow.
- Explicit rollback on service failure.
- Safe mapping to 503 when the database is unavailable.
- No partially committed support/assignment graph.

## 12.2 ML

- Trusted artifacts loaded once.
- Startup validation.
- Pinned validated runtime.
- Safe 503 if missing/corrupt.
- No raw check-in text logged on inference failure.

## 12.3 Gemini

- Explicit timeout.
- Safe fallback response.
- No retry storm.
- No dependency of CRUD, support, or local ML on Gemini availability.

## 12.4 PyOTP and Twilio SMS

- Twilio SDK calls and credentials remain server-only.
- Random TOTP secrets are authenticated-encrypted before persistence and erased when a transaction ends.
- OTP values exist only in transient backend memory and the SMS body; they are never persisted, logged, or returned by an API.
- Explicit provider timeout/error mapping uses safe errors.
- OTP transaction state prevents replay.
- Start/resend cooldowns, request-window limits, maximum verification attempts, expiry, and temporary blocking are enforced server-side.
- E.164 normalization and supported-country validation occur in Pydantic before processing.
- The browser sends the user-entered code only to FastAPI; it never calls Twilio or a client-side OTP SDK.

## 12.5 Notifications

- Written transactionally for MVP.
- No delivery claim without a real provider.
- No broker or worker dependency.

---

# 13. Testing architecture

## 13.1 Backend

Pytest and FastAPI TestClient cover:

- Signup/login/logout/refresh.
- OTP success, failure, expiry, replay, and rate limit.
- Profile ownership and one-time setup.
- Case upload validation and IDOR.
- Check-in authorization and ML integration.
- Unknown ML labels.
- `RiskEngine.NOT_CONFIGURED`.
- Gemini success/failure fallback.
- Support assignment and cross-role access.
- Notification ownership.
- Deterministic priority combinations.
- Audit creation and redaction.
- Demo seed/reset safety.

## 13.2 Frontend

Vitest and React Testing Library cover:

- Auth/session bootstrap.
- Protected and role routes.
- Form validation and async states.
- API error handling.
- Reference-faithful components.
- Empty/not-configured states.
- No prototype values rendered as real results.

E2E tests cover complete role journeys and negative authorization paths.

## 13.3 Contract tests

Frontend TypeScript response types and backend Pydantic schemas must be kept aligned through documented API contracts and integration tests.

---

# 14. Deployment topology

## MVP

```text
One frontend build
One FastAPI process
One SQLite database file
One local uploads directory
One set of trusted ML artifacts
Server-side environment/secret configuration
```

Development may run Vite and FastAPI separately with restricted CORS or a same-origin proxy. Production should preferably serve the frontend and API from the same trusted origin or through a minimal reverse proxy.

## Explicitly excluded

- Microservices.
- Kubernetes.
- Kafka.
- Redis.
- Message queues.
- Service mesh.
- Distributed tracing platform.
- Microservice API gateways.
- Unnecessary caches.

These may not be introduced without a documented production requirement and architecture review.

---

# 15. Implementation boundaries

The architecture is implemented in bounded phases:

1. Configuration, migrations, and database invariants.
2. Real authentication and authorization foundations.
3. PyOTP account-mobile OTP with Twilio SMS delivery.
4. One-time profile.
5. Reference-faithful React public/auth shell.
6. Cases and secure document storage.
7. Check-ins and local ML.
8. Gemini support.
9. Support, assignments, and notifications.
10. Priority and administrator views.
11. Role dashboards and workflows.
12. Security, accessibility, E2E, and final verification.

Each phase must preserve the module boundaries above. A feature must not be called complete until its route, service, authorization, audit behavior, frontend states, and tests are implemented together.

---

# 16. Final architectural decisions

1. **Modular monolith:** one React frontend and one FastAPI backend.
2. **Backend-authoritative security:** React guards are UX only.
3. **Layered backend:** API → Pydantic → service → SQLAlchemy/integration.
4. **Domain modules:** auth, profiles, demo personas, cases, check-ins, support, notifications, AI, ML, priority, and audit.
5. **SQLite MVP:** migrations now; PostgreSQL later only when justified.
6. **Local ML only:** trusted Joblib/scikit-learn artifacts, numeric class/confidence, unknown labels preserved.
7. **Separate risk boundary:** `RiskEngine` remains `NOT_CONFIGURED`.
8. **Deterministic priority:** verified backend facts only; never Gemini or emotion probabilities.
9. **Server-side Gemini:** official `google-genai`; no browser key exposure.
10. **Server-side PyOTP and Twilio:** the browser submits a code to FastAPI and never receives provider credentials or a verification token.
11. **Controlled demo namespace:** module-only seed/reset, every row marked, no auth bypass.
12. **No unnecessary infrastructure:** no microservices, Kafka, Redis, Kubernetes, or workers.

This is the final architecture for the SAHAYA MVP. Product code must be implemented only within these boundaries.
