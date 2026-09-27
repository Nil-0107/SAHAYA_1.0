# Running SAATHI

## Backend

```bash
cd backend
python3 -m pip install -r requirements.txt
cp .env.example .env
SAATHI_ENV=development python3 -m uvicorn app.main:app --reload
```

The API listens at `http://127.0.0.1:8000`; health is available at `/health`.

Enter real development credentials only in `backend/.env`. Never place them in `backend/.env.example`, frontend environment files, source code, or Git.

## Twilio and PyOTP OTP

The selected account-mobile OTP flow is:

```text
React → FastAPI → OtpService → PyOTP → Twilio SMS
React code submission → FastAPI → PyOTP verification
```

PyOTP generates and verifies the six-digit TOTP. Twilio only sends the SMS. React does not use a Twilio SDK or client-side OTP provider.

Configure these backend values:

```env
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SERVICE_SID=
TWILIO_API_KEY_SID=
TWILIO_API_KEY_SECRET=
TWILIO_MESSAGING_SERVICE_SID=
TWILIO_FROM_NUMBER=
SAATHI_OTP_SECRET_ENCRYPTION_KEY=
```

Use one of these Twilio authentication methods:

- `TWILIO_AUTH_TOKEN`, or
- `TWILIO_API_KEY_SID` together with `TWILIO_API_KEY_SECRET`.

Configure one SMS destination:

- `TWILIO_MESSAGING_SERVICE_SID`, or
- `TWILIO_FROM_NUMBER`.

`TWILIO_VERIFY_SERVICE_SID` remains a placeholder for a possible future Twilio Verify mode; the current PyOTP TOTP implementation uses Twilio Programmable Messaging and does not consume it.

`SAATHI_OTP_SECRET_ENCRYPTION_KEY` must be a stable, high-entropy backend-only value. It encrypts TOTP secrets before SQLite persistence. Changing it invalidates any active encrypted OTP transactions. Production startup requires this value.

Do not add Twilio credentials to `frontend/.env` or any variable beginning with `VITE_`.

## OTP lifecycle

1. Signup creates an unverified Victim/User account with an E.164 account mobile.
2. `/api/v1/auth/otp/start` generates a random TOTP secret in backend memory, encrypts it at rest, generates the current code with PyOTP, and asks the Twilio adapter to send it by SMS.
3. `/api/v1/auth/otp/verify` receives the phone and six-digit code from React, verifies it with PyOTP, consumes the transaction, erases the secret, and marks the account mobile verified.
4. The user completes the one-time profile.
5. Subsequent verified-user logins go directly through `POST /api/v1/auth/login` without OTP.

OTP expiry, start/resend cooldowns, request limits, maximum attempts, temporary blocking, and audit records are enforced by the backend. Codes, secrets, and Twilio credentials are never returned or logged.

## Demo personas

Demo accounts are seeded with both `phone_verified_at` and `profile_completed` set. They authenticate normally and never perform OTP:

From repository root:

```bash
SAATHI_ENV=development ./scripts/seed-demo.sh
```

The operation is refused for production/staging and has no HTTP endpoint.

To remove synthetic rows:

```bash
SAATHI_ENV=development ./scripts/reset-demo.sh
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set only `VITE_API_BASE_URL` and development demo-persona values through `frontend/.env`. Twilio and PyOTP secrets are backend-only.

## Verification

Backend tests use a mock Twilio provider and never send real SMS:

```bash
cd backend
SAATHI_ENV=test \
SAATHI_DATABASE_URL='sqlite:///:memory:' \
SAATHI_OTP_SECRET_ENCRYPTION_KEY='test-encryption-key' \
python3 -m pytest -q
```

Run OTP tests specifically:

```bash
SAATHI_ENV=test \
SAATHI_DATABASE_URL='sqlite:///:memory:' \
SAATHI_OTP_SECRET_ENCRYPTION_KEY='test-encryption-key' \
python3 -m pytest -q tests/test_otp.py
```

Frontend verification:

```bash
cd frontend
npm test
npm run build
```
