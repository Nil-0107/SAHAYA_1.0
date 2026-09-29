"""Explicit test-only opt-in for synthetic fixture visibility."""

import pytest


@pytest.fixture(autouse=True)
def allow_demo_fixture_data(monkeypatch: pytest.MonkeyPatch) -> None:
    # Normal development/runtime defaults to real data only. Existing demo
    # fixture tests opt in here so they continue to exercise the isolated
    # synthetic fixture graph without making it application behavior.
    monkeypatch.setenv("SAHAYA_INCLUDE_DEMO_DATA", "true")
