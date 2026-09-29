# SAHAYA Sidebar and Route Matrix

## Route guards

Frontend route guards are UX controls only. Backend role and ownership checks remain authoritative.

| Route | Allowed role | Backend integration |
|---|---|---|
| `/login` | Public | Normal login endpoint |
| `/signup/role` | Public | Public victim-only signup explanation |
| `/signup` | Public | Victim-only signup API |
| `/signup/otp` | Authenticated onboarding | OTP endpoints |
| `/profile/setup` | Authenticated onboarding | Profile endpoint |
| `/victim` | `victim` | Cases, check-ins, ML, AI, support, notifications |
| `/counsellor` | `counsellor` | Assigned requests, actions, notifications |
| `/district-officer` | `district_admin` | District assignments, requests, coordination |
| `/district-officer/operations` | `district_admin` | Counsellor appointment and assignment APIs |
| `/state-admin` | `state_admin` | State-scoped aggregate dashboard |
| `/state-admin/operations` | `state_admin` | District Administrator creation/management API |
| `/national-admin` | `national_admin` | National aggregate dashboard |
| `/national-admin/operations` | `national_admin` | State Administrator creation/management API |

## Sidebar targets

### Victim

- Dashboard/check-in: `/victim#check-in`
- AI support: `/victim#ai-support`
- My case: `/victim#my-case`
- Progress: `/victim#my-progress`
- Summary: `/victim#my-summary`
- Legal assistance boundary: `/victim#legal-assistance`
- Support: `/victim#support`

The shell notification button calls the notification API and logout calls the normal logout endpoint.

### Counsellor

- Assigned requests: `/counsellor#assigned`
- Follow-ups: `/counsellor#follow-up`
- Support actions: `/counsellor#actions`
- Notifications: shell notification panel
- Logout: shell sign-out action

Support actions post to:

```text
POST /api/v1/support-requests/{request_id}/actions
```

### District Administrator

- District dashboard: `/district-officer`
- Authorised cases: `/district-officer#cases`
- Legal coordination: `/district-officer#coordination`
- Document boundary: `/district-officer#documents`
- Appoint/manage counsellors: `/district-officer/operations`
- Assignment creation: `/district-officer/operations`
- Notifications: shell notification panel
- Logout: shell sign-out action

### State Administrator

- State dashboard: `/state-admin`
- District Administrator management: `/state-admin/operations`
- Priority queue: `/state-admin#queue`
- Notifications: `/state-admin#notifications`
- Audit log: `/state-admin#audit`
- System settings boundary: `/state-admin#settings`
- Logout: shell sign-out action

### National Administrator

- National dashboard: `/national-admin`
- State Administrator management: `/national-admin/operations`
- Priority queue: `/national-admin#queue`
- Notifications: `/national-admin#notifications`
- Audit log: `/national-admin#audit`
- System settings boundary: `/national-admin#settings`
- Logout: shell sign-out action

## Active-state behavior

`DashboardShell` derives active navigation from React Router location and hash. Exact dashboard routes use `end` matching, so `/state-admin/operations` does not incorrectly activate the dashboard item. Hash items activate only when the current hash matches.

## Route refresh behavior

All routes are React Router routes under `AuthProvider` and `ProtectedRoute`. A browser refresh restores the authenticated session through the normal refresh-cookie flow. Unauthenticated access redirects to `/login`; cross-role access redirects to `/forbidden`.

## Remaining UI limitation

Victim, counsellor, and district operational screens still use a page with anchored sections rather than separate deep-link routes for every section. The anchors are functional and refresh-safe, but the architecture's ideal route-per-section structure is not fully implemented.
