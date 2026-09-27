"""Deterministic administrative priority calculation.

This module routes authorised case work using only the structured facts in the
administrative priority specification. It does not call Gemini, interpret ML
labels, diagnose users, predict danger, or infer legal categories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final


class AdministrativePriority(str, Enum):
    HIGH = "HIGH"
    STANDARD = "STANDARD"
    REVIEW = "REVIEW"


class VerifiedHighPriorityCategory(str, Enum):
    RAPE_OR_GANG_RAPE = "RAPE_OR_GANG_RAPE"
    MURDER_GRIEVOUS_HURT_ARSON = "MURDER_GRIEVOUS_HURT_ARSON"
    WITNESS_INTIMIDATION_OR_THREATS = "WITNESS_INTIMIDATION_OR_THREATS"
    CASTE_BASED_VIOLENCE_FAMILY_AFFECTED = "CASTE_BASED_VIOLENCE_FAMILY_AFFECTED"


VERIFIED_HIGH_PRIORITY_CATEGORIES: Final[frozenset[str]] = frozenset(
    category.value for category in VerifiedHighPriorityCategory
)

_REASON_BY_FACTOR: Final[dict[str, str]] = {
    "verified_high_priority_category": "Verified high-priority case category",
    "open_protection_request": "Open protection request",
    "explicit_human_support_request": "Explicit human support request",
    "verified_wellbeing_review_flag": "Verified well-being review flag",
}


@dataclass(frozen=True, slots=True)
class PriorityFactors:
    verified_high_priority_category: bool
    open_protection_request: bool
    explicit_human_support_request: bool
    verified_wellbeing_review_flag: bool


@dataclass(frozen=True, slots=True)
class PriorityCalculation:
    priority: AdministrativePriority
    factors: PriorityFactors
    reasons: tuple[str, ...]
    internal_score: int = field(repr=False)

    @property
    def explanation(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "No qualifying administrative priority factors recorded"


class PriorityService:
    """Pure deterministic calculator for authorised administrative routing."""

    def calculate(
        self,
        *,
        verified_high_priority_category: bool,
        open_protection_request: bool,
        explicit_human_support_request: bool,
        verified_wellbeing_review_flag: bool,
    ) -> PriorityCalculation:
        factors = PriorityFactors(
            verified_high_priority_category=verified_high_priority_category,
            open_protection_request=open_protection_request,
            explicit_human_support_request=explicit_human_support_request,
            verified_wellbeing_review_flag=verified_wellbeing_review_flag,
        )
        reasons = tuple(
            reason
            for factor, reason in _REASON_BY_FACTOR.items()
            if getattr(factors, factor)
        )

        # The approved category is explicitly a high-priority factor. The other
        # approved factors are review-routing facts. A case with none of the
        # structured factors remains STANDARD. This avoids inventing thresholds
        # or combining unrelated inputs into an unstated risk score.
        if factors.verified_high_priority_category:
            priority = AdministrativePriority.HIGH
        elif reasons:
            priority = AdministrativePriority.REVIEW
        else:
            priority = AdministrativePriority.STANDARD
        internal_score = min(
            100,
            (70 if factors.verified_high_priority_category else 0)
            + (20 if factors.open_protection_request else 0)
            + (15 if factors.explicit_human_support_request else 0)
            + (10 if factors.verified_wellbeing_review_flag else 0),
        )
        return PriorityCalculation(
            priority=priority,
            factors=factors,
            reasons=reasons,
            internal_score=internal_score,
        )

    def is_verified_high_priority_category(self, *, category: str, category_verified: bool) -> bool:
        return category_verified and category.upper() in VERIFIED_HIGH_PRIORITY_CATEGORIES
