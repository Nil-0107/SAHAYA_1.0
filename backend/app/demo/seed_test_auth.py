"""Seed only local role-test accounts, without application records."""

from __future__ import annotations

import os

from app.core.config import ALLOWED_DEMO_ENVIRONMENTS, DemoSeedEnvironmentError, get_settings
from app.db.database import session_scope
from app.db.init_db import initialize_database
from app.demo.personas import DEMO_PERSONAS
from app.demo.seed_demo import _upsert, _user
from app.models import AdministrativeUnit, Role, User


TEST_AUTH_KEYS = frozenset({
    "user:victim:aarohi-demo",
    "user:counsellor:leela-demo",
    "user:district:kabir-demo",
    "user:admin:state-asha-demo",
    "user:admin:national-rohan-demo",
})


def seed_local_test_accounts(database=None) -> dict[str, int]:
    if os.getenv("SAHAYA_ENV", "").strip().lower() not in ALLOWED_DEMO_ENVIRONMENTS:
        raise DemoSeedEnvironmentError("Local test authentication seeding is blocked outside development, local, or test.")
    settings = get_settings()
    settings.require_demo_seed_allowed()
    settings.reject_obvious_production_database()
    if database is None:
        initialize_database()

    counts = {"created": 0, "updated": 0, "unchanged": 0}

    def record(result: str) -> None:
        counts[result] += 1

    with session_scope(database) as active_database:
        units = {}
        for key, name, unit_type, parent_key in (
            ("unit:state:demo", "Demo State", "state", None),
            ("unit:district:demo", "Demo District", "district", "unit:state:demo"),
        ):
            unit, result = _upsert(active_database, AdministrativeUnit, key, {
                "name": name,
                "unit_type": unit_type,
                "parent_id": units[parent_key].id if parent_key else None,
            })
            units[key] = unit
            record(result)

        personas = {persona.key: persona for persona in DEMO_PERSONAS if persona.key in TEST_AUTH_KEYS}
        order = (
            "user:admin:national-rohan-demo",
            "user:admin:state-asha-demo",
            "user:district:kabir-demo",
            "user:counsellor:leela-demo",
            "user:victim:aarohi-demo",
        )
        users: dict[str, User] = {}
        for key in order:
            persona = personas[key]
            creator = users.get("user:admin:national-rohan-demo") if persona.role == Role.STATE_ADMIN else None
            creator = users.get("user:admin:state-asha-demo") if persona.role == Role.DISTRICT_ADMIN else creator
            appointer = users.get("user:district:kabir-demo") if persona.role == Role.COUNSELLOR else None
            user, user_result, profile_result = _user(
                active_database,
                persona.key,
                full_name=persona.full_name,
                display_name=persona.display_name,
                email=persona.email,
                phone=persona.phone,
                password=persona.password,
                role=persona.role,
                language=persona.language,
                district=persona.district,
                emergency_name=persona.emergency_name,
                emergency_phone=persona.emergency_phone,
                safe_contact_method=persona.safe_contact_method,
                state_id=units["unit:state:demo"].id if persona.role != Role.NATIONAL_ADMIN else None,
                district_id=units["unit:district:demo"].id if persona.role in {Role.VICTIM, Role.COUNSELLOR, Role.DISTRICT_ADMIN} else None,
                created_by_user_id=creator.id if creator else None,
                appointed_by_user_id=appointer.id if appointer else None,
            )
            users[key] = user
            record(user_result)
            record(profile_result)

    return {**counts, "test_auth_users": len(TEST_AUTH_KEYS)}


if __name__ == "__main__":
    result = seed_local_test_accounts()
    print(f"Local test authentication accounts ready: {result['test_auth_users']}")
