# SAHAYA UI and Flow Repair

## Victim dashboard

The Victim / User dashboard is now tab-based. The sidebar changes the URL hash and only the selected section is rendered; the dashboard no longer renders every section as one long stacked page.

Supported sections:

- Overview
- Well-being check
- AI support
- My case & documents
- My progress
- My summary
- Legal assistance
- Support

## Well-being check

The check-in UI contains exactly 10 required open-ended questions. The ten answers are combined into one authenticated check-in request so the existing TF-IDF + Logistic Regression pipeline can analyze the complete reflection.

The API accepts up to 20,000 characters for this combined check-in payload.

## Case documents

The My case tab contains a working document upload workflow for PDF/JPG/JPEG/PNG files up to 10 MB. The selected case is sent to `POST /api/v1/cases/upload`, the backend validates MIME type and file signature, stores the document under a generated filename, and returns metadata which is shown in the case view.

## Registration

OTP is not required. Public victim registration uses:

- account mobile
- optional email
- date of birth
- password
- password confirmation

A newly registered account is active immediately and proceeds directly to profile setup. The account mobile is not treated as an emergency contact.

## Administrative hierarchy

- National Administrator creates State Administrators.
- State Administrator creates District Administrators within their state.
- District Administrator appoints Counsellors within their district.
- Public signup cannot create privileged roles.

## Validation

- Python backend compilation passes.
- Backend application import passes without PyOTP/Twilio dependencies.
- Frontend TypeScript type-check passes.
