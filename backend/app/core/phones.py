"""E.164 normalization for SAHAYA account-mobile numbers."""

from __future__ import annotations

import re


SUPPORTED_COUNTRIES = frozenset({"91"})
_NSN_PATTERN = re.compile(r"^[1-9]\d{6,14}$")


class PhoneNumberError(ValueError):
    pass


def normalize_account_mobile(value: str) -> str:
    raw = value.strip().replace(" ", "").replace("-", "")
    if not raw:
        raise PhoneNumberError("Phone number is required")
    if raw.startswith("00"):
        raw = f"+{raw[2:]}"
    elif raw.startswith("+"):
        raw = raw[1:]
    elif raw.isdigit() and len(raw) == 10:
        raw = f"91{raw}"
    if not raw.isdigit():
        raise PhoneNumberError("Phone number must use E.164 format")
    if not 8 <= len(raw) <= 15 or not _NSN_PATTERN.fullmatch(raw):
        raise PhoneNumberError("Phone number must use E.164 format")
    country_code = raw[:2]
    if country_code not in SUPPORTED_COUNTRIES:
        raise PhoneNumberError("Phone country code is not supported")
    national_number = raw[2:]
    if len(national_number) != 10 or national_number[0] not in "6789":
        raise PhoneNumberError("Phone number format is invalid")
    return f"+{raw}"
