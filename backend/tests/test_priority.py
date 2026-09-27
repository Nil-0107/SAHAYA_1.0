"""Deterministic administrative priority engine tests."""

from __future__ import annotations

import pytest

from app.services.priority_service import (
    AdministrativePriority,
    PriorityService,
    VERIFIED_HIGH_PRIORITY_CATEGORIES,
)


@pytest.fixture
def service() -> PriorityService:
    return PriorityService()


def test_no_structured_factors_is_standard(service: PriorityService) -> None:
    result = service.calculate(
        verified_high_priority_category=False,
        open_protection_request=False,
        explicit_human_support_request=False,
        verified_wellbeing_review_flag=False,
    )
    assert result.priority is AdministrativePriority.STANDARD
    assert result.explanation == "No qualifying administrative priority factors recorded"
    assert result.internal_score == 0


@pytest.mark.parametrize(
    ("factor", "expected_reason", "expected_score"),
    [
        ("open_protection_request", "Open protection request", 20),
        ("explicit_human_support_request", "Explicit human support request", 15),
        ("verified_wellbeing_review_flag", "Verified well-being review flag", 10),
    ],
)
def test_non_category_factors_route_to_review(
    service: PriorityService,
    factor: str,
    expected_reason: str,
    expected_score: int,
) -> None:
    values = {
        "verified_high_priority_category": False,
        "open_protection_request": False,
        "explicit_human_support_request": False,
        "verified_wellbeing_review_flag": False,
    }
    values[factor] = True
    result = service.calculate(**values)
    assert result.priority is AdministrativePriority.REVIEW
    assert expected_reason in result.reasons
    assert result.internal_score == expected_score


@pytest.mark.parametrize("category", sorted(VERIFIED_HIGH_PRIORITY_CATEGORIES))
def test_each_approved_verified_category_routes_to_high(
    service: PriorityService,
    category: str,
) -> None:
    assert service.is_verified_high_priority_category(category=category, category_verified=True)
    result = service.calculate(
        verified_high_priority_category=True,
        open_protection_request=False,
        explicit_human_support_request=False,
        verified_wellbeing_review_flag=False,
    )
    assert result.priority is AdministrativePriority.HIGH
    assert "Verified high-priority case category" in result.reasons
    assert result.internal_score == 70


def test_unverified_or_unapproved_category_is_not_high(service: PriorityService) -> None:
    assert not service.is_verified_high_priority_category(
        category="witness_intimidation_or_threats",
        category_verified=False,
    )
    assert not service.is_verified_high_priority_category(
        category="synthetic_legal_assistance",
        category_verified=True,
    )


def test_all_factors_are_capped_and_highest_priority(service: PriorityService) -> None:
    result = service.calculate(
        verified_high_priority_category=True,
        open_protection_request=True,
        explicit_human_support_request=True,
        verified_wellbeing_review_flag=True,
    )
    assert result.priority is AdministrativePriority.HIGH
    assert result.internal_score == 100
    assert result.reasons == (
        "Verified high-priority case category",
        "Open protection request",
        "Explicit human support request",
        "Verified well-being review flag",
    )
