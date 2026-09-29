# SAHAYA Repository Audit

**Audit date:** 2026-09-25  
**Scope:** Current repository only; no product features were implemented.  
**Result:** The repository is a **buildable foundation/scaffold**, not a functional or production-ready SAHAYA application.

## Executive summary

The current repository has a useful structural foundation:

- React/Vite/TypeScript/Tailwind frontend configuration and route shell.
- FastAPI application and `/health` endpoint.
- SQLAlchemy domain models for the main MVP entities.
- Scrypt password hashing/verification helpers.
- Controlled, environment-gated, idempotent synthetic demo seed/reset tooling.
- Copies of the supplied ML artifacts and a basic lazy-loading inference helper.
- Explicit placeholder boundaries for auth, OTP, Gemini, cases, support, notifications, and priority.
- Documentation, scripts, and a small active backend test suite.

However, almost all product behavior is absent:

- The backend exposes no signup, login, `/me`, OTP, profile, case, check-in, AI, support, notification, dashboard, or admin endpoints.
- The frontend has no working login/signup/OTP/profile flow and no role dashboard behavior.
- Demo password hashes exist, but the documented demo accounts cannot currently log in because no login endpoint or frontend authentication flow exists.
- Gemini and legacy OTP provider are nonfunctional stubs that always raise “not configured.”
- There is no JWT, RBAC/IDOR enforcement, audit service, notification service, support service, priority service, or `RiskEngine` interface.
- The frontend is not a faithful implementation of the supplied HTML and does not contain the required product screens/components.
- The active tests verify health and demo-data safety, not product behavior.

The current implementation should be retained as a foundation only. Product implementation should not begin by treating placeholder modules, routes, or screens as functional.

---

## Audit method and verification performed

The following read-only checks were performed:

```bash
# Backend tests
cd backend
PYTHONDONTWRITEBYTECODE=1 \
SAHAYA_ENV=test \
SAHAYA_DATABASE_URL='sqlite:///:memory:' \
python3 -m pytest -q -p no:cacheprovider

# Python dependency consistency
python3 -m pip check

# Frontend dependency install and production build
cd ../frontend
npm install --no-package-lock --no-audit --no-fund
npm run build

# Active test inventory
cd ../backend
python3 -m pytest --collect-only -q -p no:cacheprovider

# Demo idempotency
SAHAYA_ENV=test \
SAHAYA_DATABASE_URL='sqlite:///.../audit-demo.db' \
python3 -m app.demo.seed_demo
# Run again and confirm 0 created / 0 updated.

# Route inventory
python3 - <<'PY'
from app.main import app
for route in app.routes:
    print(getattr(route, "path", None), getattr(route, "methods", None))
PY
```

### Verification results

- Backend tests: **9 passed**.
- Python bytecode compilation: **passed**.
- `python3 -m pip check`: **no broken requirements**.
- Frontend TypeScript/Vite production build: **passed**.
- Frontend build output: approximately 166.6 kB JavaScript and 7.1 kB CSS before gzip.
- Demo seed first run: **39 reported creates**.
- Demo seed second run: **0 creates, 0 updates, 39 reported unchanged**.
- Actual seeded rows: **45**, not 39; the seed result excludes six profile upserts.
- FastAPI route inventory contains only:
  - `/openapi.json`
  - `/docs`
  - `/docs/oauth2-redirect`
  - `/redoc`
  - `/health`
- No active API route exists under `/api/v1`.
- No hardcoded Gemini key, legacy OTP provider authkey, JWT secret, AWS key, or private key was found in application source.
- The frontend source contains no use of `localStorage`, `sessionStorage`, `dangerouslySetInnerHTML`, `eval`, or `document.cookie`.
- The workspace is **not a Git repository**; `git status` fails.

### Environment used

```text
Python 3.14.7
Node v26.8.2
npm 11.19.1
```

Installed package versions during verification included:

```text
fastapi 0.141.1
uvicorn 0.52.4
pydantic 2.13.5
SQLAlchemy 2.0.52
joblib 1.6.0
scikit-learn 1.9.0
httpx 0.28.1
pytest 9.1.1
```

The resolved versions are not locked in the repository.

---

# 1. What already exists

## 1.1 Supplied reference artifacts

The following source materials are present in the repository root:

- `SAHAYA_OPENCODE_MASTER_BUILD_SPEC.md` — 2,186 lines.
- `sahaya_dynamic_distress_ui_updated.html` — 829 lines.
- `backend_sahaya.pdf` — six-page “SAHAYA Backend Specification.”
- `prd_sahaya(1).pdf` — four-page “SAHAYA PRD.”
- `ui_sahaya.pdf` — four-page “SAHAYA UI Specification.”
- `tfidf_vectorizer(1)(1).joblib`.
- `logistic_regression_emotion_model(1).joblib`.

The PDFs are ReportLab-generated, text-bearing PDFs. Their compressed text streams were successfully extracted to a temporary location during this audit; their requirements were compared with the master specification and current code.

The root and backend copies of each Joblib artifact are byte-for-byte identical:

```text
TF-IDF SHA-256:
9f08a8809baa607ca18e01b512f6ff3be3ab57d39cc54325d6b79305af2dde33

Logistic-regression SHA-256:
a5f886726664782cf7bec27aa7a27be27f567d457a6b246514bbf6c6f23a19cd
```

## 1.2 Frontend foundation

The required frontend directories and base configuration exist:

- React 18 + Vite + TypeScript.
- Tailwind CSS and PostCSS.
- React Router.
- Axios.
- `lucide-react` dependency.
- Required layouts:
  - `PublicLayout.tsx`
  - `AuthLayout.tsx`
  - `VictimLayout.tsx`
  - `CounsellorLayout.tsx`
  - `DistrictOfficerLayout.tsx`
  - `AdminLayout.tsx`
- Required route modules:
  - `AppRouter.tsx`
  - `ProtectedRoute.tsx`
  - `RoleRoute.tsx`
- Required service module paths.
- Required feature and component directory taxonomy.
- `AuthContext.tsx`.
- `VITE_API_BASE_URL` example.

The frontend production build succeeds, but this proves compilation only. Most feature directories contain `.gitkeep`; pages and service modules are placeholders.

## 1.3 Backend foundation

The backend contains:

- `backend/app/main.py` with a FastAPI app and `/health`.
- `backend/app/api/v1/` route-module boundaries.
- `backend/app/core/config.py` with environment and database URL settings.
- `backend/app/core/security.py` with salted scrypt password hashing/verification.
- `backend/app/core/dependencies.py` exposing only the database session dependency.
- SQLAlchemy base, engine/session setup, and explicit `create_all` helper.
- Split domain models for:
  - users
  - profiles
  - cases
  - case documents
  - check-ins
  - support requests
  - case assignments
  - support actions
  - notifications
  - OTP verifications
  - AI conversations/messages
  - audit logs
- Pydantic/schema module boundaries; almost all are placeholders.
- Service module boundaries; almost all are placeholders.
- legacy OTP provider and Gemini integration boundaries that fail explicitly when unconfigured.
- Basic upload extension/MIME/size and random-filename helpers.
- Local ML artifact loader and inference class.

## 1.4 Database and demo/persona system

The demo system is the most complete bounded feature.

Implemented controls:

- Six fictional personas covering all four supported roles.
- Clearly synthetic `.invalid` email addresses.
- Non-routable `000000...` demo phone numbers.
- Salted, non-plaintext demo password hashes.
- `is_demo` and stable `demo_key` on model records.
- Explicit `SAHAYA_ENV` requirement for seed/reset.
- Refusal for production/staging environments.
- Refusal for obvious production-looking database URLs.
- Idempotent reconciliation through stable demo keys.
- Refusal to overwrite a matching non-demo natural key.
- Transaction/savepoint rollback.
- No public seed/reset endpoint.
- Controlled reset that deletes only `is_demo=true` rows.

Actual demo record counts are:

| Model | Demo rows |
|---|---:|
| users | 6 |
| profiles | 6 |
| cases | 2 |
| case_documents | 3 |
| checkins | 4 |
| support_requests | 4 |
| case_assignments | 4 |
| support_actions | 4 |
| notifications | 8 |
| audit_logs | 4 |
| **Total** | **45** |

The displayed `Created: 39` result and current documentation incorrectly exclude the six profile rows because `_user()` creates/updates a profile but does not add that result to the counters.

## 1.5 ML artifacts and inference

The supplied artifacts were independently loaded and inspected:

- TF-IDF vectorizer:
  - `TfidfVectorizer`
  - `max_features=5000`
  - vocabulary size 5,000
- Logistic regression:
  - `LogisticRegression`
  - classes `[0, 1, 2, 3, 4, 5]`
  - coefficient shape `(6, 5000)`
  - L2 penalty
  - `max_iter=1000`
  - `random_state=42`

The current inference code correctly:

- Uses `predict_proba`.
- Selects `model.classes_[argmax]`.
- Returns numeric class and confidence.
- Keeps semantic `label=None` because training-label metadata is unavailable.

A local inference call succeeded, but loading emitted scikit-learn persistence warnings because the artifacts were created with scikit-learn 1.6.1 and the current environment has 1.9.0.

## 1.6 Documentation and scripts

Present documentation:

- `docs/REPOSITORY_AUDIT.md`
- `docs/ARCHITECTURE.md`
- `docs/ML_ARTIFACT_REPORT.md`
- `docs/DEMO_ACCOUNTS.md`
- `docs/PERSONA_TEST_REPORT.md`
- `docs/SECURITY_AUDIT.md`
- `docs/QA_REPORT.md`
- `docs/FINAL_REQUIREMENTS_MATRIX.md`
- `docs/RUNNING_SAHAYA.md`
- root and backend README files

Present scripts:

- `scripts/seed-demo.sh`
- `scripts/reset-demo.sh`

These scripts require an explicit `SAHAYA_ENV` value and call the controlled module commands.

## 1.7 Active tests

Only nine tests are collected:

- Eight demo persona/seed/safety tests.
- One health test.

All nine pass.

The files `test_auth.py`, `test_otp.py`, `test_profile.py`, `test_checkins.py`, `test_ml.py`, `test_ai.py`, `test_cases.py`, `test_support.py`, `test_notifications.py`, `test_rbac.py`, and `test_priority.py` contain a module-level skip marker but no test function. Because no tests exist in those modules, pytest does not report them as skipped; they are simply not collected.

---

# 2. What is reusable

## 2.1 Architecture and tooling

Reusable as-is or with minor cleanup:

- Mandatory top-level project structure.
- React/Vite/TypeScript/Tailwind build configuration.
- FastAPI application object and health route.
- SQLAlchemy 2.x declarative/session setup.
- SQLite foreign-key enablement.
- Domain-oriented model split.
- Optional `tsx`-compatible frontend role/layout taxonomy.
- Root `.gitignore` baseline.
- Documentation and controlled script locations.

## 2.2 Security and demo foundations

Reusable:

- Scrypt password hashing and constant-time digest comparison.
- `DemoRecordMixin` provenance approach.
- Stable demo keys and natural-key conflict refusal.
- Environment-gated seed/reset.
- No endpoint exposure for demo tooling.
- Synthetic identities and contact details.
- Transactional seed behavior.
- No fabricated ML outputs in demo check-ins.
- Explicit “not configured” integration errors.

## 2.3 ML foundations

Reusable after validation/version hardening:

- Artifact placement under `backend/app/ml/artifacts/`.
- Thread-safe lazy singleton loader.
- TF-IDF transform and `predict_proba` inference sequence.
- Numeric class/confidence response with `label=None`.
- Separation of ML from a future risk engine, although the `RiskEngine` interface itself is not yet present.

## 2.4 Reference UI design

Reusable as visual/interaction reference only:

- Color palette and typography.
- Split landing/auth composition.
- Role-card design.
- Sidebar/topbar application shell.
- Card, pill, KPI, table, timeline, progress, modal, and feedback patterns.
- Victim, counsellor, district, admin, and safety information architecture.

The old HTML must not be wrapped or shipped as the React application.

---

# 3. What is broken

## 3.1 Backend API

The backend cannot support the frontend or product:

- `/api/v1` contains no active feature routes.
- Signup, login, logout, `/me`, OTP, profile, case, check-in, AI, support, notification, dashboard, and admin routes are absent.
- `authApi.me()` in the frontend targets a nonexistent endpoint.
- CORS is not configured, so the Vite development origin cannot use the backend normally in a browser.
- No error envelope/handlers, request IDs, rate limiting, or service unavailable mapping exists.
- `/health` is a shallow process check only; it does not verify database, schema, ML artifacts, or external-service readiness.

## 3.2 Frontend authentication and routing

- `AuthContext` starts with `user=null`, hard-codes `isLoading=false`, exposes unrestricted `setUser`, and nothing in the UI establishes a real session.
- Protected role routes are therefore unreachable through normal application use.
- There is no session restoration, token/cookie strategy, refresh, logout, or login mutation.
- `AuthLayout` exists but is not used by `AppRouter`.
- No login, signup, role selection, OTP, profile setup, or account-mobile verification pages/routes exist.
- No 404 route or async error/loading states exist.

## 3.3 Frontend feature implementation

- Landing page contains only a basic project-foundation card, not the supplied auth card and role/login/signup actions.
- Victim, counsellor, district, and admin pages contain only headings.
- Components/features directories are mostly empty.
- API modules are raw Axios aliases rather than feature clients.
- API base URL configuration is duplicated between `src/config/index.ts` and `src/services/api.ts`; the exported config is unused and can drift.
- An unconditional loopback API fallback can silently produce insecure/mixed-content behavior in a deployed frontend when the environment variable is missing.
- Axios has no credential/token strategy, 401/refresh handling, error normalization, or upload-specific configuration.
- There are no forms, cards, tables, status systems, charts, modals, notifications, or accessible async states matching the reference.
- `npm audit` cannot run because no lockfile exists (`ENOLOCK`).

## 3.4 Environment handling

- The backend reads `os.getenv()` but does not load `.env` files.
- Documentation says `cp .env.example .env`, but copying the file alone does not affect backend configuration.
- Backend settings omit JWT, legacy OTP provider, Gemini, CORS, upload path, token lifetime, and rate-limit configuration.
- The PDF contract uses names such as `DATABASE_URL`; current code uses `SAHAYA_DATABASE_URL`. This is manageable but must be documented consistently.
- No fail-fast production configuration validation exists.

## 3.5 Demo seed accounting

- The database contains 45 demo rows, but the seed reports 39.
- `SeedResult.total_managed` is therefore misleading.
- Current README/docs repeat the incorrect count of 39.
- Tests assert the same incomplete counter instead of independently counting all marked rows.
- The hardcoded `demo_users=6` result is not calculated from the database.

## 3.6 Database invariants, scope, and migration behavior

- `Case` defines its own `__table_args__`, replacing the inherited demo-marker check constraint. A database-level `is_demo=true` row without `demo_key` can therefore be inserted into `cases` even though other models retain the check.
- SQLAlchemy enum columns use `native_enum=False` without explicit database check-constraint creation, so enum validation is primarily ORM-level.
- No migration system exists; `Base.metadata.create_all()` is the only schema mechanism.
- `create_all()` does not migrate an existing schema.
- No uniqueness/consistency constraint ensures a `CaseAssignment.case_id` matches its `SupportRequest.case_id`.
- The model has no formal state/national/district authorization scope. The two administrator personas differ only by profile text, and `Profile.city_or_district` is free text.
- Audit logs inherit `updated_at`, although the specification describes audit records as append-only.
- No model registry records artifact version, checksum, training metadata, or activation state.

## 3.7 Demo reset and concurrency limits

- `reset_demo()` deletes every marked demo row in its ten-model list, not only rows owned by this seed's stable-key namespace.
- Reset does not include `OTPVerification`, `AIConversation`, or `AIMessage`, even though those models also inherit demo provenance fields. Future demo OTP/AI rows could be left behind or cause foreign-key problems.
- There is no active reset test proving that all demo rows are removed and all non-demo rows are preserved.
- Two simultaneous seed processes can both miss a stable key and race on unique constraints; there is no seed lock or concurrency control.
- A demo row with the same natural key but a different `demo_key` causes a raw integrity error rather than controlled reconciliation.
- The seed preserves an existing demo password hash, so rerunning the seed does not restore a changed demo password to the documented shared value.

## 3.8 ML runtime

- Artifacts load with a version warning under the current environment.
- Requirements allow any scikit-learn version from 1.6 to below 2.0 rather than pinning a validated runtime.
- Missing artifacts are discovered only on first inference, not at application startup as required by the master specification.
- No active ML test exists.
- No check-in text-length policy is applied before inference.
- No `RiskEngine` interface or `NOT_CONFIGURED` result exists.

## 3.9 Test-suite signaling

- Feature test filenames exist but most contain no tests.
- `pytest -q` reports only nine passes and no skips, which can be mistaken for broader coverage.
- There are no frontend tests, Vitest configuration, E2E tests, security tests, or browser accessibility tests.
- No dependency vulnerability audit is possible for npm without a lockfile.
- `pip check` verifies dependency consistency, not vulnerabilities.

## 3.10 Repository process

- The workspace is not a Git repository, so the master specification’s status/diff/commit discipline cannot currently be followed.
- No Python lockfile or package hashes exist.
- No frontend lockfile exists.
- No CI configuration exists.
- No migration history exists.
- No implementation plan, API contract, or E2E report from the master sequence is present under the master-specified names.

---

# 4. What conflicts with the specifications

## 4.1 Resolved structural conflict

`backend_sahaya.pdf` describes an older `app/db/models.py` and `api/routes/` organization. The current split model files and `api/v1/` structure follow the later explicit mandatory project structure supplied by the user. The current structure should be retained; older PDF path examples should not drive a reversal.

## 4.2 Role-selection order

- The master says the first page offers login/signup and role selection follows signup.
- The supplied HTML asks for role selection before either login or signup.
- The React flow has not resolved this conflict because it has no role/auth flow.

The backend must never trust a UI-selected role for privileged authority. Privileged roles require a safe provisioning decision.

## 4.3 Optional email versus required database email

- The HTML and PRD describe email as optional during signup.
- `User.email` is currently non-null and unique.
- A real signup schema cannot satisfy optional email with the current model without a design decision.

## 4.4 Privileged self-registration

The HTML allows selection of counsellor, district officer, and administrator roles during signup. The specifications do not define invitation, allowlist, approval, or administrative provisioning. Accepting arbitrary caller-selected privileged roles would create privilege escalation. This must be resolved before auth implementation.

## 4.5 Demo phone values versus normal signup validation

The HTML validates Indian mobile numbers as `^[6-9]\d{9}$`, while demo users intentionally use `000000...` values. The demo records cannot pass a future normal phone validator. Demo identity validation and production signup validation must remain separate and clearly controlled.

## 4.6 Frontend fidelity

The current generic heading-only pages conflict with the explicit instruction not to ship a generic dashboard and not to redesign the supplied UI.

## 4.7 Unimplemented ML/risk/priority claims

The current code does not fabricate ML labels or risk scores, which is correct. However, it also lacks the required separate `RiskEngine` (`NOT_CONFIGURED`) and deterministic priority service.

## 4.8 HTML prototype behavior versus real behavior

The HTML contains intentionally fake behavior that must not be treated as a product contract:

- Any non-empty login ID/password opens a role dashboard (`sahaya_dynamic_distress_ui_updated.html:729-744`).
- OTP is generated in browser memory and displayed (`677-690`).
- Signup identity data is stored in `localStorage` (`712-715`).
- File selection is treated as successful case ingestion (`536-559`).
- Distress scores, forecasts, charts, AI summaries, legal/case facts, relief amounts, and admin metrics are hardcoded.
- Lawyers are hardcoded in the district UI (`456-464`).
- Most actions are toasts/placeholders.
- A malformed `iv>` text node exists near the auth card (`154-157`).
- Unused assessment JavaScript references undefined `questions`, `qi`, `options`, and `answered` variables (`770-789`).

The React implementation should reproduce the visual design and truthful states, not these fake actions/results.

## 4.9 PDF/backend path and environment naming differences

The extracted backend PDF uses `DATABASE_URL`, while current code uses `SAHAYA_DATABASE_URL`; the PDF also shows older model/route paths. The current mandatory structure and environment namespace can remain, but all authoritative docs must be synchronized.

## 4.10 Missing source named by the master

The master names `trd_sahaya(1).pdf`, but that exact file is absent. The supplied PDFs are generated Backend Specification, PRD, and UI Specification documents. The master also names ML files with different suffixes than the actual root files. The copied artifacts match the actual supplied files byte-for-byte, but this provenance discrepancy should be documented.

---

# 5. What is missing

## 5.1 Authentication and authorization

- Signup/login/logout endpoints.
- JWT creation, validation, expiry, revocation/refresh strategy, and secure browser token strategy.
- Current-user dependency.
- Role dependencies.
- Formal state, national, and district authorization-scope data.
- Ownership and assignment policies.
- Backend RBAC and IDOR protection.
- Privileged-role provisioning.
- Authentication audit events.
- Rate limiting and account/OTP abuse controls.
- Password policy and account lockout/throttling design.

## 5.2 OTP/legacy OTP provider

- OTP start/verify/resend endpoints.
- legacy OTP provider HTTP integration and response validation.
- Provider state mapping.
- Expiry, attempts, resend throttling, replay prevention, and consumed state.
- Tests with mocked provider.
- Frontend widget integration without exposing secrets.
- Correct account-mobile versus emergency-contact handling.

## 5.3 Profile

- Profile schemas and endpoints.
- One-time profile enforcement.
- Consent persistence through real API.
- Optional-email decision.
- Missing profile attributes identified by the supplied PRD, including relationship/case context where justified.
- Profile authorization and tests.

## 5.4 Cases and uploads

- Case creation/ingestion endpoints.
- Secure multipart handling.
- Content/file-signature inspection in addition to extension and client MIME.
- Ownership and role authorization.
- Authorized case serialization that never returns storage paths.
- Document retrieval policy.
- Real case status/timeline/updates.
- Safe empty/not-configured states for CNR, voice, and IVRS until real integrations exist.

## 5.5 Check-ins and ML

- Check-in schemas/endpoints/history.
- Authorized case linkage.
- Text validation and secure raw-text handling.
- Application startup ML validation.
- Pinned validated model runtime.
- Active fixed-sample and unknown-label ML tests.
- `RiskEngine` interface returning `NOT_CONFIGURED`.
- Model registry/provenance metadata.

## 5.6 Gemini and AI

- `google-genai` dependency.
- Server-side configuration and client lifecycle.
- Safety prompt/policy enforcement.
- Conversation/message persistence.
- Graceful fallback and error mapping.
- Mocked Gemini tests.
- Explicit immediate-danger routing behavior.
- No browser exposure of API keys or internal prompts.

## 5.7 Support, assignments, and notifications

- Support request APIs/services.
- Counsellor and district authorization scope.
- Assignment history and active assignment rules.
- Support action APIs.
- Notification generation, listing, ownership checks, and read state.
- Audit service for all sensitive/administrative actions.

## 5.8 Priority and dashboards

- Deterministic priority service.
- Verified-fact input policies.
- Human-readable reasons.
- Complete priority tests.
- Victim/counsellor/district/admin dashboard APIs.
- Real aggregates with empty states.
- Default aggregate-only administrator view.

## 5.9 Frontend product implementation

- Complete public/auth flow.
- Role selection/provisioning UX.
- Profile setup.
- Victim dashboard, check-in, AI, case, progress, support, legal information, and safety UI.
- Counsellor assigned queue and support-action UI.
- District queue, assignment, coordination, and documents UI.
- Admin aggregates, queue, authorized case inspection, and audit UI.
- Reusable components in the required taxonomy.
- Typed API services.
- Loading, empty, success, error, and retry states.
- Responsive and accessible behavior.

## 5.10 Quality and operations

- Vitest and frontend tests.
- E2E tests for the complete role journey.
- Security/IDOR/RBAC/upload/OTP replay tests.
- Alembic or another approved migration system.
- Dependency lockfiles and vulnerability scanning.
- CI.
- Git repository initialization and disciplined commits.
- Centralized structured logging/redaction.
- CORS/security headers/trusted-host/rate-limit production configuration.

---

# 6. What should be replaced

The following should be replaced during later implementation phases, not now:

1. **Frontend auth placeholder**
   - Replace the always-null `AuthContext` with a real backend-backed session strategy.
   - Do not use the old HTML’s localStorage identity flow.

2. **Frontend placeholder pages and API aliases**
   - Replace heading-only dashboards and raw Axios aliases with real feature modules and typed clients.

3. **Empty backend route/service/schema modules**
   - Implement the required modules rather than exposing them prematurely.
   - Keep the files unattached until real, authorized behavior exists.

4. **Backend environment handling**
   - Replace bare `os.getenv()` configuration with validated settings and documented environment loading.
   - Add all required secret/server-only settings without committing values.

5. **Demo result accounting**
   - Replace the 39-row reporting logic and documentation with complete model-aware counts. The seed behavior itself is reusable.

6. **ML runtime strategy**
   - Replace broad version ranges with a validated pinned/locked environment and artifact integrity/version metadata.
   - Add startup validation and real ML tests.

7. **Placeholder test files**
   - Replace marker-only files with real tests when each bounded feature is implemented.

8. **Generic frontend shell**
   - Preserve build configuration/layout boundaries, but replace generic UI with a faithful React reconstruction of the supplied visual reference.

9. **Hardcoded prototype values from the HTML**
   - Never port hardcoded scores, forecasts, case details, relief, lawyers, analytics, OTP, or login behavior as production functionality.

10. **Current documentation count/status inaccuracies**
    - Correct “39 records” to the actual complete graph count and keep status reports synchronized with executable tests.

The following should **not** be replaced casually:

- Mandatory directory structure.
- Demo `is_demo` provenance approach.
- Environment-gated module-only seed/reset.
- Synthetic persona design.
- Scrypt helper concept.
- SQLAlchemy model split.
- Actual ML artifacts and numeric-class/unknown-label contract.
- Health endpoint.
- Root documentation locations and scripts.

---

# 7. Current run commands

## 7.1 Backend

Install:

```bash
cd backend
python3 -m pip install -r requirements.txt
```

Run API:

```bash
SAHAYA_ENV=development \
python3 -m uvicorn app.main:app --reload
```

Health:

```text
http://127.0.0.1:8000/health
```

Tests:

```bash
SAHAYA_ENV=test \
SAHAYA_DATABASE_URL='sqlite:///:memory:' \
python3 -m pytest -q
```

## 7.2 Demo seed/reset

From repository root:

```bash
SAHAYA_ENV=development ./scripts/seed-demo.sh
SAHAYA_ENV=development ./scripts/reset-demo.sh
```

From backend:

```bash
SAHAYA_ENV=development python3 -m app.demo.seed_demo
SAHAYA_ENV=development python3 -m app.demo.reset_demo
```

There is intentionally no seed/reset HTTP endpoint.

## 7.3 Frontend

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
```

The frontend points to:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

No backend business endpoint currently exists under that prefix, and backend CORS is not configured, so end-to-end product calls cannot work yet.

## 7.4 Incorrect/non-working commands to avoid

- `python3 -m app.main` does not start a server; it only imports the module.
- Copying `backend/.env.example` to `.env` does not load settings automatically.
- The documented demo password cannot be used for login because no login endpoint exists.

---

# 8. Current security problems

## 8.1 Critical readiness blockers

1. **No authentication system exists.** The application cannot protect any future sensitive route. This is currently an absence of functionality rather than an exposed IDOR, but it blocks all secure product use.
2. **No RBAC/ownership/assignment enforcement exists.** The backend must not expose case, check-in, notification, support, or admin data until these controls are implemented and tested.
3. **No OTP replay/throttling/provider verification exists.** Browser/client state cannot be treated as verification.
4. **No audit service exists.** Sensitive and administrative actions cannot currently be logged.

## 8.2 Demo isolation risks

- At audit time, the demo implementation used one shared password. The implemented persona system now uses a unique password per fictional account and authenticates every persona through the normal login route.
- Safety depends on correct `SAHAYA_ENV` and database URL configuration. A production process misconfigured as `local`/`test` could pass the guard.
- The production URL check is heuristic and cannot prove that a database is non-production.
- `seed_demo(database=...)` and `reset_demo(database=...)` validate the configured environment/URL but do not verify that a caller-supplied session uses that database. A caller can pass a production-bound session while configuring a safe-looking URL.
- Demo and non-demo local-development rows share one schema. Markers and conflict guards reduce risk but do not provide physical database isolation.
- A dedicated demo database or an additional explicit opt-in is safer before wider distribution.

## 8.3 Configuration and transport

- No CORS policy exists.
- No trusted-host, CSP, HSTS, security-header, or production TLS configuration exists.
- FastAPI OpenAPI/docs are exposed by default.
- No rate limiting exists.
- No centralized request/security logging or redaction exists.
- Required server secrets are not represented in validated settings.

## 8.4 Data handling

- Check-in raw text would be stored in plaintext SQLite if the check-in API were added.
- No field-level encryption or retention policy exists for sensitive text/profile/case data.
- No authorization serializer prevents sensitive fields from reaching administrators by default.
- No log redaction is implemented beyond avoiding explicit logging in current code.

## 8.5 Password hashing

The scrypt implementation is a reasonable foundation, but:

- The encoded hash does not include explicit algorithm parameters/version.
- Future parameter changes could make old hashes unverifiable.
- There is no password policy, throttling, lockout, or breach-password check.
- There is no authenticated login flow using `verify_password`.

## 8.6 Upload security

Current helpers are not an end-to-end secure upload boundary:

- MIME type is client-declared.
- No magic-byte/content inspection exists.
- No malware scanning exists.
- No upload endpoint applies the helper.
- No authorization or ownership enforcement exists.
- No isolated storage lifecycle exists.

## 8.7 External integrations

- legacy OTP provider and Gemini do not function.
- Gemini’s placeholder accepts an API key as a function argument rather than owning server configuration.
- No redaction, timeout, retry, circuit-breaker, or provider response validation exists.

## 8.8 Dependency and artifact supply chain

- No npm lockfile; `npm audit` fails with `ENOLOCK`.
- No Python lockfile or hashes.
- No automated vulnerability scanning.
- Joblib uses pickle-based loading and requires integrity-controlled, trusted artifacts.
- Artifact provenance filename mismatch exists between the master text and actual files.
- The current scikit-learn runtime mismatch produces persistence warnings.

## 8.9 Positive security findings

- No live credentials were found in application source.
- Current React source does not store sensitive data in localStorage/sessionStorage.
- Demo seed/reset are not public API routes.
- Demo data is clearly synthetic and marked.
- Non-demo natural-key collisions are refused.
- Passwords are salted and not stored in plaintext.
- The model labels remain unknown rather than fabricated.

---

# 9. Existing demo/persona/login functionality

## 9.1 Personas

The six synthetic accounts are:

| Role | Mobile | Email |
|---|---|---|
| Victim / User | `0000000101` | `aarohi.demo@example.invalid` |
| Victim / User | `0000000102` | `meher.demo@example.invalid` |
| Counsellor / Psychologist | `0000000201` | `leela.counsellor.demo@example.invalid` |
| District Officer | `0000000301` | `kabir.district.demo@example.invalid` |
| State/National Administrator | `0000000401` | `asha.state.admin.demo@example.invalid` |
| State/National Administrator | `0000000402` | `rohan.national.admin.demo@example.invalid` |

Each account has a unique development-only password documented in `docs/DEMO_ACCOUNTS.md`. All accounts have completed profiles, synthetic phone verification timestamps, and scrypt password hashes.

## 9.2 Demo relationships

The seed creates 56 marked records:

- Two synthetic cases with timeline data.
- Four check-ins with null ML predictions.
- Three document metadata records with no storage path.
- Five support requests.
- Five case/support assignments.
- Seven support actions, including counsellor follow-up and district coordination.
- Ten notifications.
- Eight audit records, including aggregate dashboard and multiple priority examples.

The records are internally connected and idempotently reconciled.

## 9.3 Login status

Every demo persona authenticates through the normal endpoint:

```text
POST /api/v1/auth/login
```

There is no special demo login route, universal password, hidden administrator route, or authentication bypass. Login uses the same password verification, JWT issuance, account-status checks, and refresh-cookie strategy as other accounts.

## 9.4 OTP status

Demo users have a synthetic `phone_verified_at` timestamp, but:

- No OTP verification rows are seeded.
- No legacy OTP provider request occurs.
- No provider verification occurs.
- The status is fixture data, not evidence of real mobile verification.

---

# 10. Test coverage assessment

## Active and useful

- Health endpoint response.
- Demo users cover all roles.
- Demo password hashes verify.
- Demo rows are marked and keyed.
- Main entity relationships exist.
- Seed is idempotent.
- Explicit environment is required.
- Production environment and production-looking URL are refused.
- Real natural-key conflicts are not overwritten.
- Partial writes roll back on a later conflict.
- No public seed route exists.

## Missing

- Signup/login/logout/refresh/token-expiry.
- OTP provider success/failure/replay/rate limit.
- Profile authorization.
- Case upload and ownership/IDOR.
- Check-in validation and history authorization.
- ML fixed inference and unknown label.
- `RiskEngine.NOT_CONFIGURED`.
- Gemini fallback and prompt safety.
- Support/assignment/notification authorization.
- Deterministic priority combinations.
- Audit service behavior.
- CORS/CSRF/token strategy.
- Frontend route/component tests.
- Responsive/accessibility tests.
- E2E role journeys.
- Dependency vulnerability tests/scans.
- Reset behavior and preservation of every non-demo row.
- Concurrent seed execution and production-session binding safety.
- SQLite foreign-key enforcement in the test fixture.
- Database-level demo-marker constraints on every model, including `cases`.

---

# 11. Final status by required area

| Area | Current status |
|---|---|
| Repository structure | Implemented |
| Frontend build foundation | Implemented |
| Backend build foundation | Implemented |
| Health endpoint | Implemented |
| SQLAlchemy model foundation | Implemented |
| Controlled demo seed/reset | Implemented; count-reporting defect |
| Demo persona records | Implemented and synthetic |
| Demo login | Not implemented |
| Signup/auth/JWT | Not implemented |
| OTP/legacy OTP provider | Not implemented |
| Profile APIs | Not implemented |
| RBAC/IDOR controls | Not implemented |
| Victim workflows | Shell only |
| Counsellor workflows | Shell only |
| District workflows | Shell only |
| Admin workflows/analytics | Shell only |
| Case upload API | Not implemented |
| Support APIs | Not implemented |
| Notifications APIs | Not implemented |
| Audit service | Not implemented |
| ML artifact loading | Basic lazy implementation |
| ML API/tests | Missing |
| Risk engine | Missing |
| Priority service | Missing |
| Gemini | Stub only |
| Frontend Vitest | Missing |
| E2E/security tests | Missing |
| Migrations | Missing |
| Dependency locks | Missing |
| Production readiness | Not ready |

## Audit conclusion

The repository should be treated as an intentionally incomplete foundation. The strongest existing work is the synthetic demo-data isolation system, the initial model split, the safe unknown-label ML contract, and the buildable frontend/backend shells.

No product feature should be represented as complete until a real backend authorization boundary, test coverage, and the supplied UI contract are implemented. The next implementation phase should begin with database migrations/configuration and real authentication—not with frontend feature screens or placeholder API wiring.
