# SAATHI Demo Accounts

> **DEVELOPMENT-ONLY CREDENTIALS**  
> Every account and associated record below is fictional, marked `is_demo=true`, and intended only for local/development/test demonstration. Never run the demo seed against production or reuse these credentials for real accounts.

## Seed command

From the `backend` directory:

```bash
SAATHI_ENV=development python3 -m app.demo.seed_demo
```

From the repository root:

```bash
SAATHI_ENV=development ./scripts/seed-demo.sh
```

The operation is idempotent. Running it repeatedly reconciles stable `demo_key` values and does not create duplicate users or related records.

## Demo personas

| Demo role | Demo email | Demo password | Demo mobile |
|---|---|---|---|
| Victim/User | `aarohi.demo@example.invalid` | `AarohiDemo!2026` | `0000000101` |
| Victim/User | `meher.demo@example.invalid` | `MeherDemo!2026` | `0000000102` |
| Psychologist/Counsellor | `leela.counsellor.demo@example.invalid` | `LeelaDemo!2026` | `0000000201` |
| District Officer | `kabir.district.demo@example.invalid` | `KabirDemo!2026` | `0000000301` |
| State/National Administrator | `asha.state.admin.demo@example.invalid` | `AshaDemo!2026` | `0000000401` |
| State/National Administrator | `rohan.national.admin.demo@example.invalid` | `RohanDemo!2026` | `0000000402` |

Each persona has a unique password. There is no universal demo password.

## Normal authentication

All demo personas use the real authentication endpoint:

```http
POST /api/v1/auth/login
Content-Type: application/json
```

Example:

```json
{
  "identifier": "aarohi.demo@example.invalid",
  "password": "AarohiDemo!2026"
}
```

There is no special demo login endpoint, universal password, hidden administrator route, or authentication bypass. Demo provenance is not used as an authorization credential.

## Associated fictional data

The seed creates 66 marked records across the current persona graph:

- Six users and six complete profiles.
- Four synthetic victim-owned cases, including HIGH, STANDARD, and REVIEW priority-routing fixtures.
- Three fictional administrative geography units: national programme, state, and district.
- Case stage/hearing data and a fictional case timeline audit record.
- Three case-document metadata records with no real files.
- Four synthetic check-ins with no fabricated ML output.
- Five human support requests.
- Five counsellor/district assignments.
- Seven support actions, including counsellor follow-up and district coordination.
- Twelve notifications, including fictional case, support, and check-in notifications.
- Eleven audit records, including case timeline, aggregate dashboard, priority examples, and hierarchy events.

Role-specific examples:

- **Victim:** profile, cases, timeline, document metadata, multiple check-ins, support requests, and notifications.
- **Counsellor:** assigned requests, follow-up actions, and notifications.
- **District officer:** authorised access to two synthetic cases, legal/protection assistance, coordination actions, and notifications.
- **State Administrator:** aggregate-only synthetic dashboard snapshot, state scope, district-administrator management, audit visibility, and notifications.
- **National Administrator:** national aggregate scope, state-administrator management, audit visibility, and notifications.
- **Hierarchy:** the demo records persist National → State → District → Counsellor creator/appointment relationships and corresponding audit events.

## Reset procedure

From the repository root:

```bash
SAATHI_ENV=development ./scripts/reset-demo.sh
```

Or from `backend`:

```bash
SAATHI_ENV=development python3 -m app.demo.reset_demo
```

Reset is environment-gated and removes marked demo records only. It does not expose a public API endpoint.

## Safety

- All names, emails, phone numbers, cases, courts, documents, assignments, and messages are fictional.
- Email domains use the reserved `.invalid` TLD.
- Phone numbers use an intentionally non-routable `000000...` prefix.
- Production, staging, and production-looking database identifiers are refused.
- Passwords are stored using salted scrypt hashes, not plaintext.
- Demo status is provenance only and cannot grant production access.
