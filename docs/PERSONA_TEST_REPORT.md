# Persona test report

Date: 2026-09-25

## Automated coverage

- Six users cover all four supported roles.
- Every persona has a unique fictional password; no universal password is used.
- Every seeded model row is marked demo and has a stable key.
- Profiles, cases, timeline data, requests, assignments, notifications, documents, check-ins, actions, aggregate data, and audit records are related correctly.
- Demo passwords are non-plaintext and verify successfully.
- Every persona authenticates through the normal `POST /api/v1/auth/login` endpoint.
- A second seed creates no records and updates no records.
- Production environments and production-looking database URLs are refused.
- Natural-key conflicts do not overwrite real rows.
- A later conflict rolls back earlier writes through the transaction/savepoint.
- No public application route contains seed or demo functionality.
- No special login endpoint, hidden admin route, or demo authentication bypass exists.

## Result

`36 passed` in the implemented test suite.
