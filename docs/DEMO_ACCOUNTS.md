# SAHAYA Demo Accounts

> **DEVELOPMENT-ONLY CREDENTIALS**
> Every account below is fictional, marked `is_demo=true`, and intended only
> for local/development/test demonstration. Real users sign up from
> `/signup/role` with their own mobile number and password.

## Quick login

On the login page, click a role under **Select a test role** — Victim,
Counsellor, District, State Admin, National Admin — and the id + password
fill in automatically. Then choose **Log in securely**.

## Local test-auth seed

The role-login accounts are independent of synthetic application data. Seed
only those accounts with:

```bash
SAHAYA_ENV=development python -m app.demo.seed_test_auth
```

This does not create cases, check-ins, documents, support requests,
assignments, notifications, or legal records.

## Full synthetic fixture seed

From the `backend` directory:

```bash
SAHAYA_ENV=development python -m app.demo.seed_demo
```

The operation is idempotent and does not create duplicates.

Normal application runtime excludes these records. They are intended only for
explicit automated-test fixtures or an explicitly enabled demo process.

## Demo personas

| Demo role | Demo email | Demo password | Demo mobile |
|---|---|---|---|
| Victim/User | `aarohi.demo@example.invalid` | `AarohiDemo!2026` | `0000000101` |
| Victim/User | `meher.demo@example.invalid` | `MeherDemo!2026` | `0000000102` |
| Psychologist/Counsellor | `leela.counsellor.demo@example.invalid` | `LeelaDemo!2026` | `0000000201` |
| District Administrator | `kabir.district.demo@example.invalid` | `KabirDemo!2026` | `0000000301` |
| State Administrator | `asha.state.admin.demo@example.invalid` | `AshaDemo!2026` | `0000000401` |
| National Administrator | `rohan.national.admin.demo@example.invalid` | `RohanDemo!2026` | `0000000402` |
