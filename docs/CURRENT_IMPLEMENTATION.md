# SAHAYA — Current Implementation Notes

This document supersedes older audit documents that described the pre-repair OTP architecture.

## Registration

Victim/User registration requires:

- phone/mobile
- optional email
- date of birth
- password
- confirmation password

The backend creates the account as active and marks the account mobile as verified for this local product flow. No OTP provider is required.

## Gemini

The backend reads `GEMINI_API_KEY` and `GEMINI_MODEL` from `backend/.env` only.

AI chat endpoint:

`POST /api/v1/ai/chat`

AI configuration endpoint:

`GET /api/v1/ai/health`

Voice transcription endpoint:

`POST /api/v1/ai/voice/transcribe`

The adapter first uses `google-genai` and falls back to the Google Generative Language HTTP endpoint if the SDK is unavailable.

## Case workflow

`POST /api/v1/cases` creates a private case.

`POST /api/v1/cases/upload` accepts an optional `case_id`. If omitted, a private case is created automatically before the document is stored.

Accepted documents:

- PDF
- JPG/JPEG
- PNG
- maximum 10 MB

Files are stored under generated server-side filenames. Original filenames are metadata only.

## Notification workflow

Notifications are persisted in the database and returned through `/api/v1/notifications`.

A case document upload notifies the relevant national/state/district administrators and district counsellors.

A human support request notifies the relevant national/state/district administrators and district counsellors.

An assigned counsellor receives an assignment notification.

The frontend notification bell polls every 10 seconds while the authenticated dashboard is open.

## User details

Administrative user directory:

`GET /api/v1/admin/users`

Scope:

- National Administrator: national victim/user scope
- State Administrator: users in their state
- District Administrator: users in their district

Counsellor assigned-user directory:

`GET /api/v1/counsellor/users`

Only users connected to active counsellor assignments are returned.

## Hierarchy

The backend is authoritative. Frontend visibility is not treated as authorization.

```text
National Administrator
  └── creates State Administrator
        └── creates District Administrator
              └── appoints Counsellor
```

Geographic scope is checked on every administrative creation/assignment operation.
