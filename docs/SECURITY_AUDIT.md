# Security audit

## Account-mobile OTP controls

- Public signup creates only `VICTIM` accounts and stores the primary mobile in normalized E.164 format.
- The supported account-mobile country is enforced in backend Pydantic validation; frontend validation is not trusted.
- The account mobile is the only OTP target. The optional emergency contact remains a separate, unverified profile field.
- PyOTP generates and verifies a six-digit time-based code entirely in the backend.
- Twilio is used only by the backend SDK adapter to deliver the SMS. React and TypeScript never call Twilio.
- Twilio Account SID, Auth Token, API key credentials, messaging identifiers, JWT secrets, and the TOTP encryption key are backend environment settings only.
- Production startup fails when required Twilio authentication, SMS destination, JWT, or TOTP-encryption configuration is missing.
- TOTP secrets are encrypted with AES-GCM before database persistence and erased when a transaction expires, rotates, reaches its attempt limit, fails delivery, or is verified.
- Plaintext OTPs are not stored, logged, audited, or returned. API responses contain only safe success/message data.
- Start cooldown, resend cooldown, a 15-minute request window, temporary blocking, expiry, and maximum verification attempts are database-backed.
- Phone ownership is checked against the authenticated account on start, resend, and verify.
- Successful verification consumes the transaction, records `phone_verified_at`, updates account status, erases the TOTP secret, and writes an audit event.
- Twilio exceptions are mapped to safe errors without provider details or credentials.

## Authentication and demo controls

- Login uses the existing scrypt password and rotating JWT/HttpOnly refresh-session architecture.
- OTP is required only for new account-mobile verification, not for every login.
- A verified, profile-complete user reaches the dashboard through normal `POST /api/v1/auth/login` without an OTP challenge.
- Demo personas authenticate through the same login route and are seeded with `phone_verified_at` and `profile_completed` set.
- `is_demo` is provenance only and is never an authentication or authorization bypass.
- There is no OTP bypass route, universal OTP, hidden admin login, or public demo reset endpoint.
- Demo seeding remains restricted to development/local/test environments and refuses production-looking databases.

## Secret-management controls

- `.env` and `.env.*` files are ignored; `.env.example` files contain placeholders only.
- No Twilio or JWT credential has a `VITE_` prefix.
- Frontend source contains no Twilio SDK, Twilio credential setting, or client-side OTP provider script.
- Secret-bearing `Settings` fields use hidden dataclass representations to reduce accidental logging exposure.

## Test strategy

Pytest uses an in-memory SQLite database and a mock Twilio provider. No automated test sends a real SMS. Coverage includes:

- Valid TOTP verification through mocked Twilio delivery.
- Invalid and expired codes.
- Repeated invalid attempts and request-window blocking.
- Resend cooldown and secret rotation.
- Already-verified accounts.
- Malformed and duplicate E.164 phone numbers.
- Signup, OTP verification, profile setup, and subsequent normal login.
- Unverified access blocking before profile/application setup.
- Emergency-contact separation.
- Demo login without OTP.

The Twilio adapter also has a contract test using a fake Twilio client, so production SDK calls are never made by the test suite.

## Remaining operational requirements

- Real SMS delivery has not been exercised in this workspace because no actual credentials were supplied and automated tests must not send SMS.
- Production deployment must use HTTPS, a secrets manager or protected backend environment, Twilio sender/Messaging Service configuration, and a stable high-entropy `SAATHI_OTP_SECRET_ENCRYPTION_KEY`.
- Rate limits are database-backed per account. A multi-instance production deployment may additionally require a shared edge rate limiter without changing the API contract.
- Operational alerting should cover Twilio failures and repeated OTP abuse without recording OTP values or secrets.
