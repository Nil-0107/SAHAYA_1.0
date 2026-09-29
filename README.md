# SAHAYA — corrected local build

SAHAYA is a React + FastAPI well-being/support platform with a strict administrative hierarchy, local ML inference, server-side Gemini support, case-document upload, notifications, and role-scoped dashboards.

## Current implementation

- Public Victim/User signup uses **password + date of birth**. OTP/Twilio/PyOTP is not required.
- Normal login works for all seeded demo personas through the same `/api/v1/auth/login` endpoint.
- Administrative hierarchy is enforced server-side:

```text
National Administrator
        ↓
State Administrator
        ↓
District Administrator
        ↓
Counsellor
```

- National Administrators can create State Administrators.
- State Administrators can create District Administrators only inside their state.
- District Administrators can appoint Counsellors only inside their district.
- Victim/User case uploads accept PDF/JPG/JPEG/PNG up to 10 MB and automatically create a private case if the user has none.
- Case uploads and human support requests create scoped notifications for the relevant administrators/counsellors.
- Dashboards poll notifications so new events appear without a manual refresh.
- Administrators can view authorised user profile/contact/case/support/check-in metadata within their scope.
- Counsellors can view users connected to their active assignments.
- The 10-question open-ended well-being check submits all answers through the supplied TF-IDF + Logistic Regression baseline and an additional backend-only DistilBERT emotion classifier. The emotion classifier is not a distress, diagnostic, or clinically validated model.
- Voice recording uses the browser microphone and server-side Gemini transcription when `GEMINI_API_KEY` is configured.
- Gemini has both the official `google-genai` SDK path and an HTTP fallback so a missing SDK package does not silently break AI support.

## Backend

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health:

```text
http://127.0.0.1:8000/health
```

Gemini health:

```text
http://127.0.0.1:8000/api/v1/ai/health
```

Put the Gemini key **only** in `backend/.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Restart FastAPI after changing `.env`.

## Development database

The included `backend/sahaya.db` is a current-schema development database containing the synthetic hierarchy and demo records.

To recreate demo data from the current schema:

```bash
SAHAYA_ENV=development python3 -m app.db.init_db
SAHAYA_ENV=development python3 -m app.demo.seed_demo
```

Or use:

```bash
SAHAYA_ENV=development ./scripts/seed-demo.sh
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects:

```text
http://127.0.0.1:8000/api/v1
```

See `frontend/.env.development`.

## Demo accounts

See `docs/DEMO_ACCOUNTS.md`.

All demo accounts are synthetic and development-only.


## Latest integration repair

- Administrator dashboard defaults to live/non-demo data; use **Show demo data** only for testing.
- Administrator counters and escalation trend refresh automatically.
- Clicking a notification opens the linked help-seeking user's authorised details and case/document metadata. Backend scope checks remain enforced.
- Support requests are routed to the administrative hierarchy; counsellors receive case notifications after an actual active assignment rather than receiving every district request.
- Case-document uploads notify the authorised hierarchy and active assigned counsellors.
- The victim dashboard displays the latest real ML classifier confidence and a confidence trend from stored check-ins.
- The baseline classifier is the supplied TF-IDF + Logistic Regression artifact. The supplemental emotion checkpoint is `bhadresh-savani/distilbert-base-uncased-emotion` (Hugging Face revision `ce6f4ffcde7642ca2cac02381a16da38e5498ff7`), fine-tuned on the DAIR.AI Emotion six-class dataset (`sadness`, `joy`, `love`, `anger`, `fear`, `surprise`).
- Voice input uses browser SpeechRecognition when available, then recorded-audio Gemini transcription as fallback. **pyttsx3 is text-to-speech, not speech-to-text**, so it is used for the AI "Read aloud" action.
- Run `scripts/set_gemini_key.sh` to set the Gemini key without putting it in the frontend or committing it.

## Run

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
cd frontend
npm install
npm run dev
```
