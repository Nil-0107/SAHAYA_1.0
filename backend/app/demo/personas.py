"""Clearly fictional demo identities used by the controlled seed.

All email domains use the reserved ``.invalid`` TLD and all phone numbers use
an intentionally non-routable synthetic ``000000...`` prefix.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.user import Role


@dataclass(frozen=True, slots=True)
class DemoPersona:
    key: str
    full_name: str
    display_name: str
    email: str
    phone: str
    password: str
    role: Role
    language: str
    district: str
    emergency_name: str | None = None
    emergency_phone: str | None = None
    safe_contact_method: str | None = None


DEMO_PERSONAS = (
    DemoPersona(
        key="user:victim:aarohi-demo",
        full_name="Aarohi Demo (Synthetic)",
        display_name="Aarohi D.",
        email="aarohi.demo@example.invalid",
        phone="0000000101",
        password="AarohiDemo!2026",
        role=Role.VICTIM,
        language="English",
        district="Demo District / Demo City",
        emergency_name="Kiran Demo (Synthetic Support Contact)",
        emergency_phone="0000000191",
        safe_contact_method="DEMO_ONLY_NO_REAL_CONTACT",
    ),
    DemoPersona(
        key="user:victim:meher-demo",
        full_name="Meher Demo (Synthetic)",
        display_name="Meher D.",
        email="meher.demo@example.invalid",
        phone="0000000102",
        password="MeherDemo!2026",
        role=Role.VICTIM,
        language="Hindi",
        district="Demo District / Demo City",
    ),
    DemoPersona(
        key="user:counsellor:leela-demo",
        full_name="Dr Leela Demo (Synthetic)",
        display_name="Dr Leela D.",
        email="leela.counsellor.demo@example.invalid",
        phone="0000000201",
        password="LeelaDemo!2026",
        role=Role.COUNSELLOR,
        language="English / Hindi",
        district="Demo District",
    ),
    DemoPersona(
        key="user:district:kabir-demo",
        full_name="Kabir Demo (Synthetic Officer)",
        display_name="Kabir D.",
        email="kabir.district.demo@example.invalid",
        phone="0000000301",
        password="KabirDemo!2026",
        role=Role.DISTRICT_ADMIN,
        language="Hindi / English",
        district="Demo District",
    ),
    DemoPersona(
        key="user:admin:state-asha-demo",
        full_name="Asha Demo (Synthetic State Administrator)",
        display_name="Asha D. (State)",
        email="asha.state.admin.demo@example.invalid",
        phone="0000000401",
        password="AshaDemo!2026",
        role=Role.STATE_ADMIN,
        language="English",
        district="Demo State",
    ),
    DemoPersona(
        key="user:admin:national-rohan-demo",
        full_name="Rohan Demo (Synthetic National Administrator)",
        display_name="Rohan D. (National)",
        email="rohan.national.admin.demo@example.invalid",
        phone="0000000402",
        password="RohanDemo!2026",
        role=Role.NATIONAL_ADMIN,
        language="English / Hindi",
        district="Demo National Programme",
    ),
)
