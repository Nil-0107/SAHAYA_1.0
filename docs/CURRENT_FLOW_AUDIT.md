# SAHAYA Current Flow Audit

**Audit scope:** read-only inspection completed before the final correction pass. This document records the implementation that existed at the start of the correction pass, including the recently connected role dashboards and deterministic priority work. It is not an acceptance report.

## 1. Current architecture

SAHAYA is a modular FastAPI + SQLAlchemy backend with a React/Vite/Tailwind frontend.

- Backend entry point: `backend/app/main.py`
- API router composition: `backend/app/api/v1/router.py`
- Database: SQLAlchemy ORM, SQLite by default
- Authentication: JWT access tokens plus rotating HttpOnly refresh cookies
- Frontend routing: React Router with `ProtectedRoute`, `OnboardingRoute`, and `RoleRoute`
- Role dashboards: victim, counsellor, district officer, and a single administrator dashboard
- ML: local TF-IDF vectorizer and logistic-regression artifacts loaded through a lazy singleton
- AI: server-side Gemini adapter with local safe fallback
- Demo data: controlled, environment-gated SQL seed with `is_demo` and `demo_key` provenance

The project does not currently have a migration system. The available schema path is `Base.metadata.create_all()` through `backend/app/db/init_db.py`; application startup does not initialize a missing schema.

## 2. Source-of-truth inspection

The following repository sources were inspected:

- `SAHAYA_OPENCODE_MASTER_BUILD_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ML_ARTIFACT_REPORT.md`
- `docs/SECURITY_AUDIT.md`
- `docs/RUNNING_SAHAYA.md`
- `docs/DEMO_ACCOUNTS.md`
- `docs/REPOSITORY_AUDIT.md`
- `sahaya_dynamic_distress_ui_updated.html`
- `prd_sahaya(1).pdf`
- `ui_sahaya.pdf`
- `backend_sahaya.pdf`

The master build specification and architecture document are the clearest executable contracts. The referenced TRD file is not present in the workspace. The PDF sources were not rendered during this audit; repository documentation and the master specification were used for the recorded findings.

The uploaded root ML artifacts and the runtime copies are both present:

- `tfidf_vectorizer(1)(1).joblib`
- `logistic_regression_emotion_model(1).joblib`
- `backend/app/ml/artifacts/tfidf_vectorizer.joblib`
- `backend/app/ml/artifacts/logistic_regression_emotion_model.joblib`

## 3. Current backend routes

### Health

- `GET /health`
- `GET /api/v1/health`
- FastAPI documentation routes `/docs`, `/redoc`, and `/openapi.json` are currently exposed.

Health routes are liveness-only. They do not verify database, ML artifact, upload storage, Twilio, or Gemini readiness.

### Authentication and profile

- `POST /api/v1/auth/signup` — public; currently victim-only
- `POST /api/v1/auth/login` — public
- `POST /api/v1/auth/refresh` — refresh-cookie authenticated
- `POST /api/v1/auth/logout` — bearer authenticated
- `GET /api/v1/me` — bearer authenticated
- `POST /api/v1/auth/otp/start`
- `POST /api/v1/auth/otp/resend`
- `POST /api/v1/auth/otp/verify`
- `POST /api/v1/profile`
- `GET /api/v1/profile`
- `PATCH /api/v1/profile`

### Cases, check-ins, and AI

- `POST /api/v1/checkins`
- `GET /api/v1/checkins/me`
- `GET /api/v1/checkins/{checkin_id}`
- `POST /api/v1/ai/chat`
- `POST /api/v1/cases/upload`
- `GET /api/v1/cases/me`
- `GET /api/v1/cases/{case_id}`

There is currently no general case-creation endpoint.

### Support and notifications

- `POST /api/v1/support-requests` — victim only, existing owned case required
- `GET /api/v1/support-requests/me`
- `GET /api/v1/support-requests/{request_id}`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/read-all`
- `POST /api/v1/notifications/{notification_id}/read`

### Current role dashboards and administration

- `GET /api/v1/counsellor/dashboard`
- `GET /api/v1/district/dashboard`
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/queue`
- `GET /api/v1/admin/cases/{case_id}`
- `POST /api/v1/admin/cases/{case_id}/priority-recalculate`

The administrator dashboard and priority endpoints currently use the single `ADMIN` role. They do not distinguish state and national authority.

### Required routes currently absent

The following routes from the supplied architecture/master contracts are not implemented:

- `POST /api/v1/ai/case-extract`
- `GET /api/v1/support-requests/assigned`
- `POST /api/v1/support-requests/{id}/actions`
- Case-assignment creation and assignment-history routes
- `GET /api/v1/admin/audit`
- `GET /api/v1/dashboard/victim`
- `GET /api/v1/dashboard/counsellor`
- `GET /api/v1/dashboard/district`
- `GET /api/v1/dashboard/admin`
- Administrative account creation/provisioning routes
- Administrative deactivation/reactivation routes
- Operational notification creation routes

## 4. Current frontend routes

`frontend/src/routes/AppRouter.tsx` currently defines:

- `/`
- `/login`
- `/signup/role`
- `/signup`
- `/signup/otp`
- `/profile/setup`
- `/victim`
- `/counsellor`
- `/district-officer`
- `/admin`
- `/forbidden`
- unmatched route fallback

The current frontend uses one large page per role with hash anchors instead of the complete route structure described by the UI/architecture contract.

### Victim navigation

The victim layout points to hash sections on `/victim`:

- `#check-in`
- `#ai-support`
- `#my-case`
- `#my-progress`
- `#my-summary`
- `#legal-assistance`
- `#support`

There are no separate routes for check-in, case, support, notifications, profile, or AI history.

### Counsellor navigation

The counsellor layout points to:

- `#assigned`
- `#follow-up`
- `#actions`

There are no separate assigned-request, case-detail, support-action, or notification routes.

### District navigation

The district layout points to:

- `#cases`
- `#coordination`
- `#documents`
- `#users`

`#users` has no corresponding section. There is no counsellor appointment form, assignment mutation, case-detail route, or document retrieval route.

### Administrator navigation

The administrator layout points to:

- `#queue`
- `#model-health`
- `#cases`
- `#audit`

Only the queue section is currently represented. The other administrator sidebar targets are dead or incomplete links.

### Common shell

`frontend/src/components/navigation/DashboardShell.tsx` provides:

- Role-specific sidebar rendering
- Active state based on the current route/hash
- Notification loading and read actions
- Logout
- Responsive shell behavior

Notifications are loaded on mount. There is no polling or real-time update.

## 5. Current database entities

Implemented SQLAlchemy models include:

- `User`
- `Profile`
- `Case`
- `CaseDocument`
- `Checkin`
- `SupportRequest`
- `CaseAssignment`
- `SupportAction`
- `Notification`
- `OTPVerification`
- `AIConversation`
- `AIMessage`
- `AuditLog`

Important current relationship facts:

- A `Case` has one owner and can have documents, check-ins, support requests, assignments, notifications, and AI conversations.
- A `SupportRequest` belongs to a user and case.
- A `CaseAssignment` links a case, support request, assignee, and assigning user.
- A `SupportAction` belongs to a support request and actor.
- Notifications are user-owned and may optionally reference a case.
- Audit records are append-oriented in application behavior, but append-only behavior is not enforced by the database.

There is no formal state, national-scope, or district-scope entity. `Profile.city_or_district` is free text. There is no `state_id`, `district_id`, `created_by`, or `appointed_by` administrative hierarchy relationship on `User`.

There is no case-update/event entity. Real case timelines are not persisted; demo timeline data is read from special audit metadata.

## 6. Current role system and authorization

The current backend role enum is:

```text
VICTIM
COUNSELLOR
DISTRICT_OFFICER
ADMIN
```

There are no distinct:

```text
STATE_ADMIN
NATIONAL_ADMIN
DISTRICT_ADMIN
```

roles.

Public signup is restricted to victims. This prevents arbitrary administrative-role creation, but privileged accounts can currently be created only through direct database access or the demo seed. No secure administrative provisioning chain exists.

Current role checks use `require_roles(...)`, with resource ownership checks in individual services. Examples:

- Cases and check-ins are owner-scoped.
- Support requests are victim-owned or assignment-scoped for counsellors/district officers.
- The single administrator role currently receives global support-request access.
- Counsellor and district dashboards derive visibility from active assignments.
- Administrator dashboard queries global aggregates.

The requested hierarchy is not represented:

```text
NATIONAL ADMINISTRATOR
        ↓
STATE ADMINISTRATOR
        ↓
DISTRICT ADMINISTRATOR
        ↓
COUNSELLOR
```

## 7. Current authentication implementation

Implemented controls:

- Salted scrypt password hashes
- Short-lived signed JWT access tokens
- Rotating HttpOnly refresh cookies
- Refresh-token hash storage
- Session-version revocation
- Generic login errors
- Dummy password verification for unknown accounts
- PyOTP account-mobile verification
- AES-GCM encrypted OTP secrets
- OTP cooldown, expiry, attempt limits, and secret erasure
- Backend-owned account-mobile checks
- Public signup restricted to victim accounts

Important gaps:

- No login/signup/refresh/AI rate limiting beyond OTP-specific controls.
- No concurrent OTP compare-and-set or row-lock consumption.
- One refresh-token hash per user means multiple sessions invalidate one another.
- Production refresh-cookie security and JWT algorithm settings are not fail-closed.
- No formal startup schema/migration check.
- `backend/.env` is not loaded by the current settings implementation, despite runtime documentation referring to it.

## 8. Current ML implementation

Relevant files:

- `backend/app/ml/loader.py`
- `backend/app/ml/inference.py`
- `backend/app/services/checkin_service.py`
- `backend/app/services/ml_service.py`
- `backend/tests/test_ml.py`

Current behavior:

- Uses the supplied TF-IDF and logistic-regression joblib artifacts.
- Loads artifacts through process-level lazy singletons.
- Does not retrain or refit during inference.
- Uses `predict_proba` when available.
- Returns numeric model classes only.
- Leaves semantic labels unknown/null.
- Does not convert emotion classification into a diagnosis, risk score, or danger probability.
- Returns safe unavailable errors when artifacts are missing or corrupt.
- Stores check-in text and model output in the check-in record.

Current ML gaps:

- No startup artifact validation.
- No checksum or artifact manifest verification.
- No model registry/version record persisted with each check-in.
- No explicit `RiskEngine` boundary.
- No `NOT_CONFIGURED` risk-engine result.
- Artifact persistence-version compatibility warnings remain.
- Inference failure does not create a retryable failed check-in record.
- ML failure handling and model metadata need a single consistent contract.

## 9. Current AI and safety implementation

Relevant files:

- `backend/app/api/v1/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/integrations/gemini.py`
- `frontend/src/pages/victim/DashboardPage.tsx`
- `frontend/src/components/modals/SafetyModal.tsx`

Current controls:

- Gemini key remains server-side.
- Official `google-genai` adapter is used.
- Conversation ownership is checked.
- Prompt and provider errors are not returned to the browser.
- Safe fallback is returned on provider failure.
- Manual immediate-danger modal exists.

Current gaps:

- No deterministic immediate-danger detection/routing from AI input.
- No case-extraction endpoint.
- No conversation history/list endpoint.
- AI request quota/rate limit is absent.
- Safety post-processing is based on limited exact fragment checks and is not a complete safety boundary.
- No robust policy for diagnosis, legal conclusions, prompt disclosure, or false emergency/lawyer/police contact claims.
- No provider timeout/circuit breaker.
- AI is available to any ready role rather than a deliberately defined role set.

## 10. Current case and support flows

### Cases

Implemented:

- Owner-scoped case list/detail
- Secure random filenames
- MIME/signature checks
- 10 MB upload limit
- Storage-path suppression
- Audit writes

Missing/broken:

- No case creation flow for a newly registered victim.
- No document download/retrieval route.
- No real case timeline persistence.
- No case update workflow.
- No case cancellation or replacement flow.
- Database constraints do not enforce all owner/case relationships.

### Support

Implemented:

- Victim support request creation for an existing owned case
- Assignment-scoped counsellor/district reads
- Seeded support actions and notifications

Missing/broken:

- No assignment creation API.
- No assignment history API.
- No support action creation API.
- No support status transition/resolution API.
- No operational notification creation.
- New real support requests cannot enter staff queues without an external assignment write.
- The single administrator role can read all raw support details through support endpoints, bypassing the aggregate-only administrator policy.

## 11. Current priority implementation

Relevant files:

- `backend/app/services/priority_service.py`
- `backend/app/schemas/admin.py`
- `backend/app/services/admin_service.py`
- `backend/app/api/v1/admin.py`

The deterministic calculator accepts only structured backend facts:

- Verified approved category
- Open protection request
- Explicit human support request
- Verified well-being review flag

It returns `HIGH`, `STANDARD`, or `REVIEW`, with human-readable reasons. The internal weighted score is capped at 100 and is not returned by the API.

The current demo seed includes fictional cases representing all three outcomes.

Current priority gaps:

- Support request creation still writes a fixed `standard` string and does not invoke the case-level priority service.
- New protection requests do not update `Case.protection_request_open`.
- Priority recalculation is transient and does not persist a priority result or audit event.
- The administrator queue and support-priority fields use different concepts.
- The escalation trend reads raw support priority strings rather than the deterministic case-level result.

## 12. Current demo system

The demo seed is environment-gated and marks records with `is_demo`/`demo_key`. It contains six synthetic users and a connected fictional case/support graph. Demo users authenticate through the normal `/api/v1/auth/login` endpoint; no demo login bypass exists.

Current demo limitations relevant to the requested hierarchy:

- Demo state and national personas use the same ambiguous `ADMIN` role.
- They do not have persisted `created_by`/`appointed_by` hierarchy relationships.
- Demo district scope is represented by profile text rather than a formal scope relationship.
- The demo graph does not model all required administrative creation/appointment events.
- The current seed has 60 managed records after the priority fixture expansion.
- Demo reset is broad and does not yet have complete coverage for every future demo child record.

## 13. Broken and incomplete flows

1. New real victim signup cannot create a case, so the case/document/support flow cannot start normally.
2. A new support request has no assignment or notification workflow.
3. Assigned counsellors cannot create support actions or update statuses through the API.
4. District and administrator operational mutation flows are absent.
5. State and national administrative levels do not exist.
6. Administrative provisioning and deactivation/reactivation flows do not exist.
7. Several required frontend subroutes do not exist; sidebars are mostly hash links.
8. Admin sidebar has dead targets.
9. District sidebar has a dead `#users` target.
10. No browser E2E tests cover complete user flows.
11. No formal role-route matrix exists.
12. No migration/startup schema verification exists.
13. ML metadata and controlled lifecycle validation are incomplete.
14. AI safety and rate limiting are incomplete.
15. Administrator support access is broader than the aggregate/privacy contract.

## 14. Duplicate and stale implementations

- `backend/app/services/ml_service.py` is a compatibility alias for the real ML implementation in `backend/app/ml/inference.py`.
- `backend/app/services/audit_service.py` is only a boundary while services write `AuditLog` directly.
- `backend/app/services/gemini_service.py` is an empty boundary while the real implementation is split between `ai_service.py` and `integrations/gemini.py`.
- `backend/app/utils/files.py` contains file helpers that are not the active upload implementation.
- Case timeline data is stored in audit metadata rather than a case event table.
- Route modules perform substantial direct queries instead of keeping all domain access in services.
- The old HTML prototype remains in the repository and must not be treated as production code.
- Several README, QA, requirements, and audit documents are stale relative to the current implementation.

## 15. Security problems requiring correction

Highest priority:

1. Replace ambiguous administrator authority with explicit hierarchy roles and geographic scope.
2. Remove unrestricted administrator access to raw support-request data.
3. Add backend-enforced administrative provisioning and geographic validation.
4. Add audit records for all administrative creation/deactivation/appointment actions.
5. Add missing assignment/support-action workflows with role and scope checks.
6. Add login/signup/refresh/AI abuse controls.
7. Add schema initialization/migration validation.
8. Add controlled ML artifact validation and model metadata.
9. Improve AI safety and immediate-danger routing.
10. Add browser, route, RBAC, and complete flow tests.

## 16. Audit conclusion

The current application has a real backend-authoritative authentication, OTP, owner-scoped data, ML artifact, Gemini, dashboard, notification, and demo foundation. It is not yet compliant with the requested strict administrative hierarchy or complete UI flow requirements.

The correction pass must preserve the existing architecture and extend it. The next implementation phase should begin with explicit role/scope models and secure administrative account provisioning, followed by missing operational assignment/support flows, then frontend route/sidebar integration, then ML/AI lifecycle and safety corrections, followed by full API, browser, build, and security verification.
