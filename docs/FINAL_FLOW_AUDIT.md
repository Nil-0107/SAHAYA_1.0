# SAHAYA Final Flow Audit

This document records the implemented state after the correction pass. It is intentionally evidence-based: a flow is called complete only where backend/frontend code and automated tests support it.

## Authentication and onboarding

Implemented and tested:

- Public victim-only signup
- JWT access session
- Rotating HttpOnly refresh cookie
- Login/logout/refresh
- PyOTP/Twilio account-mobile OTP flow
- Profile setup
- Frontend auth restoration and protected routing
- Explicit administrative roles in the backend enum
- Public administrative-role rejection

The real Twilio delivery path still requires provider credentials. Tests use a provider double and do not send real SMS.

## Role hierarchy

Implemented and tested:

```text
NATIONAL_ADMIN → STATE_ADMIN → DISTRICT_ADMIN → COUNSELLOR
```

Implemented backend endpoints:

- State Administrator creation/listing by National Administrator
- District Administrator creation/listing by State Administrator
- Counsellor appointment/listing by District Administrator
- Account suspension/reactivation with parent-role and geographic checks
- Database notification and audit event for every administrative account operation
- Persisted state/district/creator/appointment relationships

Raw support content is no longer available to administrators through the generic support-request endpoint.

## Victim flow

Implemented:

- Landing → signup → OTP → profile → victim dashboard routing
- Private case creation
- Owner-scoped case list/detail
- Secure document upload
- Check-in submission/history
- Real ML artifact inference
- AI support through server-side Gemini adapter/fallback
- Support request creation
- Notifications
- Immediate-danger routing from AI input to the existing configured-resource safety modal

Not fully implemented:

- Document download/retrieval
- Real case timeline mutation for non-demo cases
- Progress/summary generation
- Legal chatbot/IVRS/external integrations

These remain truthful empty/not-configured states rather than mock functionality.

## Counsellor flow

Implemented:

- Assignment-scoped dashboard
- Assigned request list
- Follow-up/support-action list
- Persisted support-action creation
- Request status update through the action endpoint
- Notifications
- Logout

## District flow

Implemented:

- District-scoped dashboard
- Authorised case summaries
- Assistance requests
- Coordination records
- Notifications
- Counsellor appointment/management UI
- Assignment creation UI and backend endpoint
- District aggregate/audit visibility

Not fully implemented:

- Court/government/lawyer integrations
- Document retrieval
- Dedicated case-detail route
- External emergency/authority contact

## State and National flow

Implemented:

- Shared aggregate administrator dashboard
- State-scoped and national-scoped backend queries
- State Administrator management UI/API
- District Administrator management UI/API
- Audit visibility
- Notifications
- Logout

The state and national dashboards intentionally share the aggregate dashboard component rather than duplicating dashboard implementations.

## ML

Implemented:

- Actual supplied TF-IDF and logistic-regression artifacts
- Thread-safe lazy singleton loading
- 5000-feature/vectorizer and class `{0..5}` validation
- `predict_proba` confidence when supported
- Null semantic labels
- Persisted model version
- No diagnosis/risk/legal conversion
- Frontend numeric class/confidence display

Known limitation: no signed artifact manifest or persistent model registry exists. The installed scikit-learn version emits a persistence-version warning for the supplied artifact.

## Sidebar/navigation

Implemented:

- Explicit role routes for victim, counsellor, district, state, and national users
- Functional management routes for state/national/district administration
- No dead administrator sidebar targets
- No dead district `#users` target
- Route/hash active state derived from React Router location
- Loading/error/empty states on connected API pages
- Notification and logout actions in the common shell

Known limitation: victim/counsellor/district sections remain anchored sections inside role pages rather than separate deep-link routes for every section.

## Security status

Implemented controls:

- Backend role dependencies
- Geographic scope checks
- Ownership checks
- Public administrative-role rejection
- Raw administrator support-content restriction
- Process-local auth/AI rate limits
- OTP controls
- Secure cookie production configuration checks
- Backend-only Gemini/Twilio credentials
- Safe provider/model error responses
- Audit minimization

Known limitations:

- Rate limiting is process-local, not distributed.
- Joblib artifacts are not checksum/signature verified.
- OpenAPI remains enabled.
- No browser E2E/security scanning pipeline is present.
- Additional database cross-entity constraints and retention policies are not yet implemented.

## Test evidence

Latest executed:

- Backend: `107 passed`
- Frontend: `29 passed`
- Frontend TypeScript/Vite production build: passed
- Assignment/support-action API flow: passed
- Hierarchical provisioning/geographic scope tests: passed
- ML artifact/inference tests: passed
- Demo seed/idempotency tests: passed
- Existing role/ownership/OTP/auth/cases/support/notification/AI tests: passed

Known warnings:

- Starlette/httpx deprecation
- Google GenAI Python deprecation
- scikit-learn persistence-version warning
- React Router future-flag warnings
- Four moderate npm advisories
