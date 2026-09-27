# SAATHI — OpenCode Master Build Specification
## PRD + TRD + UI Contract + Backend Contract + ML Contract + Agent System + Sequential Prompts

> **Purpose:** This document is the single implementation contract for OpenCode.
>
> The target is to reproduce the supplied SAATHI UI faithfully as a production-style React application and connect it to a corresponding FastAPI backend.
>
> **Do not redesign the product. Do not invent missing ML capabilities. Do not silently expand scope.**

---

# 0. SOURCE-OF-TRUTH ORDER

OpenCode MUST use sources in this priority order:

1. This document.
2. `trd_saathi(1).pdf` — supplied Technical Requirements Document.
3. `saathi_dynamic_distress_ui_updated.html` — visual/interaction reference.
4. Actual uploaded ML artifacts:
   - `logistic_regression_emotion_model(1)(2).joblib`
   - `tfidf_vectorizer(1)(1)(1).joblib`
5. Existing repository code, only where it does not contradict the above.

If two sources conflict, STOP and report the conflict before making a major architectural decision.

The supplied TRD specifies React + Vite + TypeScript, Tailwind, FastAPI, SQLAlchemy, SQLite for MVP, JWT/password hashing, local scikit-learn/joblib, server-side Gemini, Axios, React Router, pytest and Vitest. It also explicitly says new frontend code should not reuse the old HTML/JS implementation. The implementation should therefore reproduce the supplied HTML's visual/interaction design in React rather than simply wrapping or shipping the old HTML. [Source: supplied TRD, pages 1–2.]

---

# 1. NON-NEGOTIABLE ENGINEERING RULES

## 1.1 Do not make assumptions

Never invent:

- ML class meanings
- distress labels
- clinical diagnoses
- legal conclusions
- case verification
- emergency-service contact
- police contact
- counsellor contact
- risk scores
- user data
- analytics numbers
- API responses
- database records

If a capability is not backed by a real backend/service/model, show a truthful unavailable/not-configured state.

## 1.2 UI fidelity

The supplied `saathi_dynamic_distress_ui_updated.html` is the visual reference.

Preserve:

- overall layout
- visual hierarchy
- navigation
- typography feel
- colors
- cards
- buttons
- status pills
- forms
- spacing
- responsive behavior
- role selection
- dashboard structure
- interaction flow

Do not replace it with a generic admin template.

Do not make a generic Tailwind dashboard.

Do not redesign the product.

React + Tailwind is the implementation technology; the old HTML is a visual reference, not production frontend code.

## 1.3 Backend is authoritative

The frontend must never be the security boundary.

The backend performs:

- authentication
- authorization
- role checks
- ownership checks
- case access checks
- support-request permissions
- file validation
- OTP verification
- ML inference
- priority calculation
- audit logging

Hiding a React button is NOT authorization.

## 1.4 Secrets

Never put these in frontend source:

- Twilio Account SID, Auth Token, API key credentials, and messaging identifiers
- TOTP encryption key and TOTP secrets
- Gemini API key
- JWT secret
- database credentials
- service credentials

Twilio credentials and TOTP secret-encryption material are backend-only. Do not copy any real values into source or frontend environment files.

Use `.env` locally and a secret manager in production.

---

# 2. PRODUCT REQUIREMENTS DOCUMENT — PRD

## 2.1 Product

SAATHI is a multi-role support platform with:

- account creation/login
- mobile verification
- profile setup
- victim/user well-being check-ins
- local ML emotion inference
- optional AI support through server-side Gemini
- human support requests
- case/document management
- legal assistance flows
- protection/safety request flow
- counsellor workflow
- district officer workflow
- administrator analytics/queue
- audit logging

## 2.2 Roles

### Victim / User

Can:

- sign up
- verify own account mobile
- complete profile
- add optional emergency contact
- submit well-being check-ins
- view own check-in history
- use AI support
- request human support
- request legal support
- request protection/relocation support
- manage own case
- upload authorised case documents
- view authorised case information
- view notifications

Cannot:

- access another user's records
- alter another user's case
- access admin/counsellor-only data
- manipulate priority
- decide their own authorisation

### Psychologist / Counsellor

Can, within authorization scope:

- view assigned well-being requests
- view authorised case context
- view authorised check-ins
- manage follow-up
- record support actions
- update support status

Cannot:

- access arbitrary users
- access unrelated cases
- access admin-only analytics

### District Officer

Can, within authorization scope:

- view authorised assistance requests
- review authorised cases
- coordinate legal/protection assistance
- assign/manage authorised legal support
- view authorised district-level information
- review documents/court updates where authorised

Cannot:

- access unrestricted private user information
- access other district scopes unless explicitly authorized

### State / National Administrator

Can, within authorization scope:

- view aggregate programme analytics
- view authorised queue
- inspect authorised case data
- recalculate deterministic priority
- administer supported configuration
- inspect audit logs
- monitor system/model health

Administrators should see aggregates by default, not raw sensitive user content.

---

# 3. ACCOUNT AND OTP REQUIREMENTS

## 3.1 First page

The first page must present:

- Log in
- Sign up

After Sign up, user selects role.

Role cards:

- Victim / User
- Psychologist / Counsellor
- District Officer
- State / National Administrator

The UI must preserve the existing role-card design.

## 3.2 Signup

Flow:

1. Role selection
2. Full name
3. Account mobile number
4. Email
5. Password
6. Confirm password
7. Create account
8. Send account-mobile OTP
9. OTP verification
10. Account setup
11. Optional emergency contact
12. Complete setup
13. Dashboard

## 3.3 CRITICAL: account mobile != emergency contact

These are two separate fields/concepts.

### Account mobile

Used for:

- account identity
- signup OTP
- login/recovery mechanisms where implemented

### Emergency contact

Used only as a support/contact relationship.

It must NOT be substituted for the user's account mobile.

The account-mobile OTP verification must never silently verify the emergency contact.

The UI must visibly distinguish:

`Account mobile — Verified`

from:

`Emergency contact — Optional / configured`

---

# 4. PYOTP + TWILIO OTP CONTRACT

## 4.1 Server-side OTP generation

PyOTP generates and verifies the six-digit time-based code in the FastAPI backend. The browser never runs a client-side OTP provider and never receives a TOTP secret.

The backend creates a random TOTP secret for each transaction, encrypts it before persistence, sends the current code through the server-only Twilio SMS adapter, and erases the secret when the transaction ends.

## 4.2 Twilio delivery

Twilio credentials exist only in the backend environment. React sends requests only to FastAPI; FastAPI calls Twilio.

Use Twilio Programmable Messaging with one of:

- a configured Messaging Service SID; or
- a configured Twilio sender number.

The browser may never call Twilio directly.

## 4.3 Backend verification

The user submits the account mobile and six-digit code to FastAPI. OtpService verifies the code with PyOTP, checks the active database transaction, expiry, phone ownership, and attempt count, then consumes the transaction.

The API never returns the code, TOTP secret, Twilio credentials, or a provider verification token.

## 4.4 OTP states

Support:

- pending
- sent
- verifying
- verified
- expired
- invalid
- provider_error
- rate_limited

## 4.5 Never trust frontend success alone

Only successful backend PyOTP verification may mark the account mobile verified. Frontend validation, Twilio delivery success, or a browser state transition is not verification.

---

# 5. UI CONTRACT — REFERENCE SCREENS

The supplied HTML contains these major screens and interactions.

## Public

### Landing

Heading:

`A quiet support layer through the case journey.`

Welcome card:

`Welcome to SAATHI`

Buttons:

- Log in
- Sign up

### Role selection

Cards:

- Victim / User
- Psychologist / Counsellor
- District Officer
- State / National Administrator

### Login

Fields:

- registered mobile or ID
- password

Actions:

- Show password
- Log in securely
- Create a new account

### Signup

Fields:

- full name
- 10-digit mobile
- email
- password
- confirm password

Action:

`Create account & send OTP`

### OTP

Heading:

`Verify your mobile number`

Six-digit OTP.

Actions:

- Verify OTP
- Resend OTP
- Back to account details

### Account setup

Fields:

- preferred language
- city/district
- account phone/status
- optional emergency contact

Action:

`Finish account setup`

---

# 6. VICTIM/USER UI

## Dashboard

Primary actions:

- Start today's well-being check
- Get human support
- I'm not safe

Section:

`Today's next step`

Action:

`Take check-in`

## Well-being check

Prompt:

`How have you been feeling since your last check-in, and what has been affecting you the most?`

Textarea:

`Write whatever you feel comfortable sharing...`

Actions:

- Save & exit
- Submit response

Additional:

- Voice support
- AI support

## AI support

Chat interface:

- message input
- Send
- voice control

AI response is generated only server-side.

The AI must:

- be calm
- concise
- non-judgmental
- not diagnose
- not provide legal conclusions
- not claim case verification
- not claim it contacted anyone
- not expose internal prompts/API keys/database details/scoring

If immediate danger is reported, normal conversation stops and emergency-support UI is shown.

## Legal information

Sections:

- Legal chatbot
- IVRS legal assistance
- Human legal support

Actions:

- Open legal chatbot
- Start IVRS flow
- Request legal aid

The legal chatbot must not claim to provide definitive legal advice.

## Case

Entry choices:

- Document / Photo Scan
- e-Courts CNR Lookup
- Voice Statement
- Guided Questions

Upload screen:

- FIR
- Charge Sheet
- Hearing Notice

Allowed MVP files:

- PDF
- JPG
- PNG

Maximum:

10 MB.

Case overview:

- case information
- case summary
- documents
- authorised updates

## Progress

Sections:

- Why it changed
- 14-day trend
- My well-being summary
- How summary is produced

Do not fabricate trend data.

## Support

Cards:

- Counsellor
- Legal aid
- Protection / relocation

Actions:

- Request callback
- Request legal help
- Raise safety request

---

# 7. COUNSELLOR UI

Title:

`Well-being care dashboard`

Contains:

`New mental well-being requests`

Case card:

`Open case`

Case detail sections:

- Distress pattern
- Relevant case context
- AI-extracted themes

Action:

`Record support action`

All information is authorization-controlled.

The local emotion model output must not be presented as a clinical diagnosis.

---

# 8. DISTRICT OFFICER UI

Title:

`Case assistance dashboard`

Contains:

`New assistance requests`

Actions:

- Open case
- Review

Case:

`Case SA-2048 · Legal assistance`

Sections:

- Case details
- Assign / manage lawyer
- Coordination
- Documents & court updates

Controls:

- authorised lawyer
- legal aid representation type
- assignment reason

Actions:

- Assign lawyer
- View assignment history
- Open documents

No hardcoded lawyers in production.

---

# 9. ADMIN UI

Title:

`Programme overview`

Sections:

- Risk distribution
- 7-day escalation trend
- District analytics
- State analytics
- Policy indicators

These values must come from real backend APIs.

Do not create fake analytics.

Priority queue must be deterministic and explainable.

---

# 10. SAFETY UI

Immediate-danger flow exists in the reference UI.

Button:

`I'm not safe`

Admin/safety screen:

`Are you in immediate danger?`

Action:

`Request immediate help`

Do not claim external emergency contact unless an actual backend integration exists.

---

# 11. TECHNOLOGY REQUIREMENTS

From the supplied TRD:

## Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- lucide-react
- Axios
- React Router

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite for MVP
- PostgreSQL later

## Auth

- JWT
- password hashing
- secure token strategy
- do not use localStorage for sensitive tokens if avoidable

## ML

- scikit-learn
- joblib

## GenAI

- google-genai
- server-side only

## Files

- local filesystem for MVP
- database stores metadata
- files outside frontend

## Testing

- pytest
- FastAPI TestClient
- Vitest

---

# 12. REPOSITORY STRUCTURE

```text
saathi/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   ├── api/
│   │   │   └── routes/
│   │   └── services/
│   │       ├── ml_service.py
│   │       ├── gemini_service.py
│   │       ├── case_service.py
│   │       └── priority_service.py
│   ├── models/
│   │   ├── logistic_regression_emotion_model.joblib
│   │   └── tfidf_vectorizer.joblib
│   ├── uploads/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
├── README.md
├── agents.md
└── .gitignore
```

---

# 13. DATABASE

Minimum MVP entities from the supplied TRD:

```text
users
profiles
cases
case_documents
checkins
support_requests
audit_logs
```

Recommended additions required by the full UI:

```text
otp_verifications
notifications
case_assignments
support_actions
ai_conversations
ai_messages
model_registry
```

Important user fields:

```text
users
- id
- email
- phone
- password_hash
- role
- phone_verified_at
- profile_completed
- created_at
- updated_at
```

Profile:

```text
profiles
- id
- user_id
- full_name
- display_name
- preferred_language
- city_or_district
- emergency_contact_name
- emergency_contact_phone
- safe_contact_method
- consent_at
```

Case:

```text
cases
- id
- owner_user_id
- case_number
- category
- category_verified
- stage
- court_name
- next_hearing
- summary
- protection_request_open
- created_at
- updated_at
```

Case document:

```text
case_documents
- id
- case_id
- owner_user_id
- filename
- mime_type
- storage_path
- extracted_json
- uploaded_at
```

Check-in:

```text
checkins
- id
- user_id
- case_id
- text
- predicted_class
- predicted_label
- confidence
- created_at
```

Support request:

```text
support_requests
- id
- user_id
- case_id
- type
- status
- priority
- explicit_human_request
- created_at
- resolved_at
```

Audit:

```text
audit_logs
- id
- actor_user_id
- action
- resource_type
- resource_id
- created_at
- metadata_json
```

---

# 14. API CONTRACT

Required endpoints:

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
GET  /api/v1/me

POST /api/v1/auth/otp/start
POST /api/v1/auth/otp/verify
POST /api/v1/auth/otp/resend

POST /api/v1/profile
PATCH /api/v1/profile

GET  /api/v1/cases/me
POST /api/v1/cases/upload
GET  /api/v1/cases/{id}

POST /api/v1/checkins
GET  /api/v1/checkins/me

POST /api/v1/ai/chat
POST /api/v1/ai/case-extract

POST /api/v1/support-requests

GET  /api/v1/admin/queue
GET  /api/v1/admin/cases/{id}
POST /api/v1/admin/cases/{id}/priority-recalculate

GET  /api/v1/notifications
POST /api/v1/notifications/{id}/read

GET  /api/v1/dashboard/victim
GET  /api/v1/dashboard/counsellor
GET  /api/v1/dashboard/district
GET  /api/v1/dashboard/admin

GET /health
```

Every protected endpoint requires valid authentication.

Every resource endpoint performs ownership/role authorization on the backend.

---

# 15. ACTUAL ML ARTIFACT CONTRACT

The supplied artifacts were inspected.

## Logistic regression

Type:

`sklearn.linear_model.LogisticRegression`

Configuration:

- penalty = l2
- max_iter = 1000
- random_state = 42

Actual classes:

```text
[0, 1, 2, 3, 4, 5]
```

Features:

```text
5000
```

Coefficient shape:

```text
(6, 5000)
```

## TF-IDF

Type:

`sklearn.feature_extraction.text.TfidfVectorizer`

Configuration:

```text
max_features = 5000
```

Vocabulary size:

```text
5000
```

## Inference

```python
X = vectorizer.transform([text])
probabilities = model.predict_proba(X)[0]
class_id = model.classes_[probabilities.argmax()]
confidence = float(probabilities.max())
```

## CRITICAL LABEL RULE

The model artifacts establish six numeric classes.

They do NOT by themselves establish the semantic meaning of those six classes.

Never invent:

```text
0 = sadness
1 = anger
...
```

If training metadata can be recovered, create:

```text
backend/app/config/ml_labels.json
```

Otherwise keep:

```text
label = null
```

and expose class IDs internally only.

---

# 16. ML SERVICE

Create:

```text
WellbeingService
```

Requirements:

- load vectorizer once
- load logistic model once
- fail startup clearly if required artifacts are missing
- do not reload models per request
- validate text
- run inference
- return class ID and confidence
- optionally return label only if verified

Output:

```json
{
  "class_id": 2,
  "label": null,
  "confidence": 0.71
}
```

The model is an emotion classifier.

It must NOT be described as:

- clinical diagnosis
- suicide detector
- mental-health diagnosis engine
- definitive distress detector

unless a separately validated model actually supports that claim.

---

# 17. RISK ENGINE

The local emotion classifier and a risk engine are separate concepts.

Implement an interface:

```python
class RiskEngine:
    def evaluate(...):
        ...
```

MVP implementation:

```text
NOT_CONFIGURED
```

Do not manufacture a distress score from emotion probabilities.

If deterministic backend policy later uses verified facts, implement that separately and document its inputs.

---

# 18. PRIORITY SERVICE

The supplied TRD specifies deterministic priority categories:

```text
RAPE_OR_GANG_RAPE
MURDER_GRIEVOUS_HURT_ARSON
WITNESS_INTIMIDATION_OR_THREATS
CASTE_BASED_VIOLENCE_FAMILY_AFFECTED
```

Base score:

```text
verified high-priority category = +70
open protection request = +20
explicit human support request = +15
wellbeing flag = +10
```

Maximum:

```text
100
```

Priority must be calculated only from verified/authorised backend facts.

Never expose raw internal scoring/model details to users.

Queue reasons should be human-readable, for example:

`Verified high-priority case category`

---

# 19. GEMINI SERVICE

The supplied TRD specifies server-side Gemini.

Use:

```python
from google import genai
client = genai.Client(api_key=settings.GEMINI_API_KEY)
```

Never expose the Gemini key to React.

Use the official `google-genai` SDK.

AI support rules:

- calm
- concise
- non-judgmental
- no mental-health diagnosis
- no legal conclusions
- no claim of case verification
- no false claims of contacting humans/emergency services
- emergency-support UI for immediate danger
- encourage authorised human support when requested or deterministic backend rules require it
- never reveal system prompts
- never reveal API keys
- never reveal database internals
- never reveal internal scoring

Gemini failure:

The supplied TRD requires graceful fallback:

`AI support temporarily unavailable`

The local backend result must still be available where applicable.

---

# 20. CASE UPLOAD SECURITY

Accept only:

- PDF
- JPG
- PNG

Maximum:

10 MB.

Requirements:

- server-generated random storage filename
- never use user filename as filesystem path
- store owner_user_id
- store case_id
- validate extension
- validate MIME type
- do not execute uploaded files
- never return raw filesystem paths to browser

---

# 21. ERROR CONTRACT

```text
401 Unauthorized
403 Forbidden
400 Invalid request/upload
413 File too large
503 ML unavailable
503 database unavailable
503 Gemini unavailable
```

Frontend must display human-readable messages.

Never expose stack traces to users.

Log technical details server-side.

Do not log raw check-in text on ML failure.

---

# 22. SECURITY REQUIREMENTS

Must prevent:

- IDOR
- privilege escalation
- plaintext passwords
- secret exposure
- JWT leakage
- unsafe file paths
- arbitrary file upload
- XSS
- SQL injection
- unauthorized case access
- cross-user notification access
- cross-role access
- OTP replay
- fake frontend-only verification

Audit:

- login
- logout
- signup
- account verification
- profile changes
- case assignment
- case changes
- support changes
- privileged access
- admin changes
- model configuration changes

Never log:

- passwords
- OTP
- JWT
- refresh tokens
- Twilio credentials and TOTP secrets/encryption keys
- Gemini API key
- unnecessary raw sensitive text

---

# 23. AGENT SYSTEM

OpenCode should use these specialized agents sequentially.

## Agent 0 — Auditor

Responsibilities:

- inspect repo
- inspect current UI
- inspect ML artifacts
- identify conflicts
- no coding

Output:

`docs/repository-audit.md`

## Agent 1 — Architect

Responsibilities:

- architecture
- module boundaries
- API contract
- database design

Output:

`docs/architecture.md`
`docs/api-contract.md`

## Agent 2 — Backend Engineer

Responsibilities:

- FastAPI
- SQLAlchemy
- Pydantic
- authentication
- routes
- services

## Agent 3 — Database Engineer

Responsibilities:

- models
- migrations
- constraints
- indexes

## Agent 4 — OTP/Security Engineer

Responsibilities:

- PyOTP and Twilio
- signup verification
- account phone verification
- token security

## Agent 5 — ML Engineer

Responsibilities:

- Joblib
- TF-IDF
- Logistic Regression
- inference
- label metadata
- risk-engine interface

## Agent 6 — Frontend Engineer

Responsibilities:

- React
- TypeScript
- Tailwind
- routing
- UI fidelity
- API integration

## Agent 7 — QA/Security Engineer

Responsibilities:

- unit tests
- integration tests
- E2E
- RBAC
- IDOR
- security audit
- UI regression

No agent may silently modify unrelated areas.

---

# 24. GIT DISCIPLINE

Before every phase:

```bash
git status
git diff
```

Create a commit after a successful phase.

Recommended commits:

```text
chore: initialize saathi architecture
feat: add database foundation
feat: add authentication
feat: add pyotp twilio otp verification
feat: add wellbeing ml service
feat: add checkin workflow
feat: add support workflow
feat: integrate victim ui
feat: integrate counsellor ui
feat: integrate district ui
feat: integrate admin ui
test: add security and e2e coverage
docs: finalize implementation documentation
```

If an agent modifies files outside its task, stop and inspect the diff.

---

# 25. DEFINITION OF DONE

The system is NOT done until:

- landing works
- login works
- signup works
- role selection works
- account mobile OTP works through backend verification
- account setup works
- emergency contact is separate
- victim dashboard works
- check-in works
- actual supplied ML artifacts are used
- ML artifacts are loaded once
- unknown labels are not fabricated
- risk engine is clearly separate
- AI support works through server-side Gemini where configured
- Gemini failure is handled
- case upload works securely
- case details work
- support request works
- counsellor workflow works
- district workflow works
- admin workflow works
- priority is deterministic
- notifications work
- audit logging works
- RBAC works
- IDOR tests pass
- frontend is responsive
- no secrets are in source
- tests pass
- documentation is accurate

---

# 26. OPEN CODE EXECUTION RULES

Before coding:

1. Inspect.
2. Plan.
3. Show intended files.
4. Implement one bounded phase.
5. Test.
6. Review diff.
7. Commit.
8. Stop.

Never:

- rebuild everything blindly
- delete working code without inspection
- replace the UI with a generic template
- fabricate ML labels
- fabricate data
- put secrets in React
- use frontend role checks as security
- add unrequested dependencies
- change database architecture silently
- switch frameworks
- rewrite the product based on personal preference

---

# 27. SEQUENTIAL OPENCODE PROMPTS

Use these prompts ONE AT A TIME.

## PROMPT 01 — AUDIT

```text
You are Agent 0, the senior repository auditor.

Read completely:

- SAATHI_MASTER_SPEC.md
- trd_saathi(1).pdf
- saathi_dynamic_distress_ui_updated.html
- logistic_regression_emotion_model(1)(2).joblib
- tfidf_vectorizer(1)(1)(1).joblib

Inspect the entire repository.

Do not modify application code.

Inspect:
- frontend
- backend
- database
- auth
- UI
- APIs
- ML
- dependencies
- environment
- tests

Inspect both Joblib artifacts with Python.

Determine:
- model type
- vectorizer type
- classes
- feature count
- vocabulary size
- available metadata

Do not guess class meanings.

Create:
docs/repository-audit.md
docs/implementation-plan.md

Report conflicts between the supplied TRD and current repository.

STOP after the audit.
```

## PROMPT 02 — ARCHITECTURE

```text
You are Agent 1, the SAATHI architect.

Use SAATHI_MASTER_SPEC.md as the implementation contract.

Create:
docs/architecture.md
docs/api-contract.md
docs/database-schema.md

Define:
- React architecture
- FastAPI architecture
- database
- auth
- RBAC
- PyOTP and Twilio
- ML service
- risk engine
- Gemini service
- case management
- support
- notifications
- audit logging
- file storage

Do not code features yet.

Do not redesign the UI.

STOP.
```

## PROMPT 03 — FOUNDATION

```text
Implement only the backend/frontend project foundation.

Frontend:
React + Vite + TypeScript + Tailwind + React Router + Axios + lucide-react.

Backend:
FastAPI + SQLAlchemy + Pydantic.

Create clean folder structure.

Add configuration and health endpoint.

Do not implement business features.

Run tests/build.

STOP.
```

## PROMPT 04 — DATABASE

```text
Implement the database layer from docs/database-schema.md.

Create:
users
profiles
cases
case_documents
checkins
support_requests
audit_logs
otp_verifications
notifications
case_assignments
support_actions
ai_conversations
ai_messages
model_registry

Use SQLite for MVP.

Add constraints, indexes and relationships.

Do not add fake production data.

Run migrations and tests.

STOP.
```

## PROMPT 05 — AUTH

```text
Implement authentication.

Include:
- signup
- login
- password hashing
- JWT
- refresh/logout if specified
- /me
- role authorization
- protected routes

Do not implement OTP yet.

Do not use plaintext passwords.

Do not use frontend-only authorization.

Write tests.

STOP.
```

## PROMPT 06 — PYOTP + TWILIO OTP

```text
Implement account-mobile OTP verification.

Generate and verify a six-digit TOTP with PyOTP in the backend.

Send the generated code through Twilio Programmable Messaging.

Twilio credentials must exist ONLY in the backend environment.

The browser must never call Twilio or receive a TOTP secret, Twilio credential, provider token, or OTP value from the API.

Signup remains unverified until backend PyOTP verification succeeds.

Account mobile and emergency contact are separate.

Implement start/verify/resend OTP endpoints, abuse controls, and tests with a mock Twilio provider.

STOP.
```

## PROMPT 07 — PROFILE

```text
Implement one-time account setup.

Fields:
- preferred language
- city/district
- optional emergency contact

Do not use emergency contact as account verification.

Add profile create/update APIs.

Add authorization and tests.

STOP.
```

## PROMPT 08 — ML

```text
Implement WellbeingService using the actual uploaded Joblib artifacts.

Vectorizer:
TfidfVectorizer(max_features=5000)

Classifier:
LogisticRegression with six classes [0,1,2,3,4,5].

Load both once.

Use predict_proba.

Do not invent label meanings.

If training metadata is unavailable, return class_id and label=null.

Create a separate RiskEngine interface.

MVP risk engine must be NOT_CONFIGURED.

Add tests.

STOP.
```

## PROMPT 09 — CHECKIN

```text
Implement check-in API.

Flow:
authenticated user
→ validate text
→ save check-in
→ run actual local ML
→ save prediction
→ return safe result

Do not call emotion prediction a clinical diagnosis.

Do not fabricate distress scores.

Add history endpoint.

Add tests.

STOP.
```

## PROMPT 10 — GEMINI

```text
Implement server-side Gemini support using google-genai.

Never expose Gemini key to frontend.

Implement AI chat.

Follow the supplied AI safety constraints.

If Gemini fails:
return a safe fallback such as:
AI support temporarily unavailable

Do not fabricate external actions.

Add tests with mocked Gemini.

STOP.
```

## PROMPT 11 — CASES

```text
Implement case management.

Support:
- My Case
- case upload
- case details
- case documents
- authorised updates

Accept only PDF/JPG/PNG.

Maximum 10 MB.

Generate server-side storage filenames.

Never expose filesystem paths.

Add ownership tests.

STOP.
```

## PROMPT 12 — SUPPORT

```text
Implement:
- human support request
- legal support request
- protection/relocation request
- support status
- support actions
- notifications

Add role authorization.

Do not create fake external contacts.

Add tests.

STOP.
```

## PROMPT 13 — PRIORITY

```text
Implement deterministic priority service exactly from the supplied TRD.

Use only verified backend facts.

Maximum score 100.

Provide human-readable reason.

Never expose raw internal model/scoring details.

Add tests for every category and combination.

STOP.
```

## PROMPT 14 — FRONTEND SHELL

```text
Now implement the React frontend.

Use the supplied saathi_dynamic_distress_ui_updated.html only as the visual reference.

Do NOT copy its old JS architecture.

Reproduce its UI faithfully in React + TypeScript + Tailwind.

Implement:
- landing
- login
- signup
- role selection
- OTP
- profile setup
- protected routing
- role routing

Do not redesign.

Do not use generic templates.

STOP after visual validation.
```

## PROMPT 15 — VICTIM UI

```text
Implement the Victim/User UI from the reference.

Connect real APIs for:
- dashboard
- check-in
- history
- AI support
- legal information
- case
- progress
- support
- notifications

No hardcoded production data.

Unknown ML labels must remain unknown.

STOP.
```

## PROMPT 16 — COUNSELLOR UI

```text
Implement the counsellor UI from the reference.

Connect:
- wellbeing requests
- assigned cases
- authorised check-ins
- support actions
- follow-up
- notifications

Enforce backend authorization.

STOP.
```

## PROMPT 17 — DISTRICT UI

```text
Implement the District Officer UI from the reference.

Connect:
- assistance requests
- case details
- lawyer assignment
- coordination
- documents
- court updates
- notifications

No hardcoded lawyer data in production.

STOP.
```

## PROMPT 18 — ADMIN UI

```text
Implement the State/National Administrator UI from the reference.

Connect:
- programme overview
- risk distribution
- escalation trend
- district analytics
- state analytics
- policy indicators
- priority queue
- authorised case view
- priority recalculation
- audit information

All analytics must be real backend data.

STOP.
```

## PROMPT 19 — SECURITY

```text
Perform a complete security audit.

Test:
- IDOR
- role escalation
- unauthorized cases
- cross-user check-ins
- cross-user notifications
- OTP replay
- token expiry
- secret exposure
- unsafe file upload
- XSS
- SQL injection
- CORS
- rate limits

Fix findings.

Create docs/security-review.md.

STOP.
```

## PROMPT 20 — E2E

```text
Run complete E2E flow:

signup
→ account mobile OTP
→ profile setup
→ dashboard
→ check-in
→ ML inference
→ AI support
→ case upload
→ support request
→ counsellor
→ district
→ admin
→ audit log

Also test negative authorization/security flows.

Fix failures.

Create docs/e2e-test-report.md.

STOP.
```

## PROMPT 21 — UI QA

```text
Compare the React application against saathi_dynamic_distress_ui_updated.html.

Test:
1440
1280
1024
768
480
360

Check:
- spacing
- colors
- typography
- cards
- navigation
- buttons
- forms
- OTP
- dashboards
- mobile layout
- accessibility
- horizontal overflow

Fix only actual regressions.

Do not redesign.

STOP.
```

## PROMPT 22 — FINAL AUDIT

```text
You are now an independent senior reviewer.

Read all documentation and inspect actual code.

For every requirement report:

PASS / PARTIAL / FAIL

Audit:
- auth
- OTP
- account mobile vs emergency contact
- RBAC
- ML
- Gemini
- cases
- support
- priority
- notifications
- audit
- security
- UI fidelity
- responsive design
- tests

Do not hide failures.

Fix issues that can be fixed without inventing requirements.

Create:
docs/FINAL-AUDIT.md

Do not declare production-ready if a critical security, authorization, OTP, data-integrity or core UI requirement fails.

STOP.
```

---

# 28. FINAL COMMAND TO OPENCODE

Only after all phases:

```text
Do a final clean-room verification.

Start from the actual current repository state.

Do not trust previous agent claims.

Run:
- backend tests
- frontend tests
- type checking
- build
- API smoke tests
- ML inference test
- OTP integration test with mocked provider
- RBAC tests
- upload security tests
- E2E tests

Inspect git diff.

Search the entire repository for:
- API keys
- authkeys
- passwords
- tokens
- TODO
- FIXME
- fake data
- hardcoded dashboard numbers
- hardcoded case records
- fake ML labels
- console.log containing sensitive data

Then produce the final audit.

STOP.
```

---

# 29. IMPORTANT SCOPE BOUNDARY

The supplied UI/TRD includes more than the two local ML artifacts.

Therefore OpenCode must treat these as separate capabilities:

```text
Local ML:
TF-IDF + Logistic Regression
        ↓
emotion class + confidence

Gemini:
server-side generative AI
        ↓
AI support / case extraction

Deterministic backend rules:
verified facts
        ↓
priority

Human workflow:
support requests
        ↓
counsellor / legal / protection workflow
```

Never collapse these into one fake "AI risk model."

---

# 30. FINAL SUCCESS CONDITION

The finished product should feel like the supplied SAATHI UI, but be implemented as:

```text
React + TypeScript + Tailwind
             ↓
          Axios
             ↓
           FastAPI
             ↓
 ┌───────────┼────────────┐
 ↓           ↓            ↓
SQLite      Local ML     Gemini
 ↓           ↓            ↓
cases     wellbeing    AI support
users     inference    case extraction
support
audit
```

The old HTML is the visual reference.

The React application is the actual frontend.

The FastAPI application is the security and business-logic authority.

The supplied Joblib files are the actual local ML artifacts.

No fabricated model capability is permitted.
