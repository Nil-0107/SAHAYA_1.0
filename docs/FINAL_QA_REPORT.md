# SAHAYA Final QA Report

## Test commands

### Backend

```bash
cd backend
SAHAYA_ENV=test \
SAHAYA_DATABASE_URL='sqlite:///:memory:' \
SAHAYA_OTP_SECRET_ENCRYPTION_KEY='test-encryption-key' \
python3 -m pytest -q
```

Result: **107 passed**.

### Frontend

```bash
cd frontend
npm install
npm test
npm run build
```

Result:

- **29 frontend tests passed**
- TypeScript project build passed
- Vite production build passed

## Verified flows

- Normal victim login and role routing
- Public signup administrative-role rejection
- OTP/profile/session tests
- Demo seed creation/idempotency
- National → State → District → Counsellor provisioning
- Cross-state and cross-district rejection
- Account status management
- District/counsellor assignment workflow
- Support action and status workflow
- Case creation and ownership
- Secure case upload
- Real ML artifact inference
- Gemini adapter and safe fallback
- AI immediate-danger routing signal
- Administrator raw-support privacy boundary
- State/national/district aggregate scope
- Notification owner scope
- Deterministic priority outcomes
- Frontend route guards and demo role routing

## Warnings and advisories

- Starlette/httpx deprecation warning
- Google GenAI Python deprecation warning
- scikit-learn persistence-version warning for the supplied artifact
- React Router future-flag warnings
- Four moderate npm audit advisories
- No real Twilio SMS was sent during tests
- No real Gemini request was made without configured credentials

## Not verified / remaining limitations

- No Playwright/Cypress/browser E2E suite exists.
- No live Twilio delivery verification.
- No live Gemini delivery verification.
- No distributed rate limiter or production-grade session store.
- No signed ML artifact manifest or model registry table.
- No document download/retrieval route.
- No real case timeline mutation endpoint.
- No external government, court, police, emergency, lawyer, or IVRS integration.
- Victim/counsellor/district section navigation uses anchored pages rather than a separate route for every section.
- Database migrations are still represented by `Base.metadata.create_all()` rather than a versioned migration system.

## Acceptance status

The implemented acceptance items are backed by the test/build evidence above. The project should not be described as production-ready until the remaining limitations—particularly browser E2E, distributed security controls, signed model artifacts, and external-provider verification—are addressed.
