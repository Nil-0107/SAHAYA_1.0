# SAHAYA RBAC Hierarchy

## Implemented hierarchy

```text
NATIONAL_ADMIN
      ↓ creates
STATE_ADMIN
      ↓ creates
DISTRICT_ADMIN
      ↓ appoints
COUNSELLOR
```

`VICTIM` is the public user-facing role and is not part of the administrative appointment chain.

The backend role enum uses explicit values:

```text
victim
counsellor
district_admin
state_admin
national_admin
```

Legacy local enum names `ADMIN` and `DISTRICT_OFFICER` remain aliases only for compatibility with existing local test/database callers. Application authorization code uses the explicit values.

## Geographic scope

`backend/app/models/administrative_unit.py` stores national, state, and district units with parent relationships.

`User` stores:

- `state_id`
- `district_id`
- `created_by_user_id`
- `created_role`
- `appointed_by_user_id`
- `appointed_at`

The controlled demo seed creates a connected graph:

```text
Demo National Programme
  └── Demo State
        └── Demo District
              ├── Demo District Administrator
              ├── Demo Counsellor
              └── Demo Victims
```

## Backend permissions

| Role | Allowed administrative actions |
|---|---|
| `NATIONAL_ADMIN` | Create/list/suspend/reactivate State Administrators; create district coordination assignments; view national aggregate dashboard and scoped audit |
| `STATE_ADMIN` | Create/list/suspend/reactivate District Administrators within `state_id`; view state aggregate dashboard and scoped audit |
| `DISTRICT_ADMIN` | Appoint/list/suspend/reactivate Counsellors within `district_id`; create counsellor assignments within district; view district aggregate dashboard and scoped audit |
| `COUNSELLOR` | Read assigned requests/actions; create support actions/status updates for active assigned requests |
| `VICTIM` | Manage own profile/check-ins/cases; create own support requests; read own notifications |

## Provisioning endpoints

```text
POST /api/v1/admin/state-administrators       NATIONAL_ADMIN only
GET  /api/v1/admin/state-administrators       NATIONAL_ADMIN only

POST /api/v1/admin/district-administrators    STATE_ADMIN only
GET  /api/v1/admin/district-administrators    STATE_ADMIN only

POST /api/v1/admin/counsellors                DISTRICT_ADMIN only
GET  /api/v1/admin/counsellors                DISTRICT_ADMIN only

PATCH /api/v1/admin/accounts/{id}/status     Parent administrator only
```

Every successful creation writes:

- User and profile
- Scope relationship
- Creator/appointment relationship
- Database notification
- Audit event with actor, action, target, timestamp, role metadata, and scope IDs

Passwords and OTPs are never written to audit metadata.

## Public signup

Public signup accepts only `victim`. Administrative values are not public credentials. Requests attempting to submit an administrative role are rejected by the backend.

## Scope enforcement

- State Administrator district creation requires `actor.state_id == target_state_id`.
- District Administrator counsellor appointment requires `actor.district_id == target_district_id`.
- Assignment creation verifies both target-account scope and case-owner scope.
- District/counsellor dashboards and support reads verify district scope when the authenticated account has a district scope.
- State/national aggregate dashboards filter case-owner state/district scope.
- Generic administrator support endpoints return no raw victim support content.

## Tests

`backend/tests/test_administration_hierarchy.py` covers:

- National → State → District → Counsellor creation
- Creator/appointment persistence
- Database notifications
- Audit events
- Cross-state rejection
- Cross-district rejection
- Unauthorized role rejection
- Assignment and support-action flow
- Administrator raw-support privacy boundary
