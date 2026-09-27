"""Password hashing and JWT-safe token helpers.

The application uses a versioned scrypt format. The verifier also accepts the
original three-part demo format so existing controlled demo hashes remain
usable during development.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User


_HASH_SCHEME = "scrypt"
_HASH_VERSION = "v1"
_HASH_N = 2**14
_HASH_R = 8
_HASH_P = 1
_HASH_DKLEN = 32


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_HASH_N,
        r=_HASH_R,
        p=_HASH_P,
        dklen=_HASH_DKLEN,
        maxmem=64 * 1024 * 1024,
    )
    return "$".join(
        (
            _HASH_SCHEME,
            _HASH_VERSION,
            str(_HASH_N),
            str(_HASH_R),
            str(_HASH_P),
            _encode(salt),
            _encode(digest),
        )
    )


def _scrypt_digest(
    password: str,
    salt: bytes,
    *,
    n: int,
    r: int,
    p: int,
    dklen: int,
) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=dklen,
        maxmem=64 * 1024 * 1024,
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        parts = encoded.split("$")
        if len(parts) == 7 and parts[0] == _HASH_SCHEME and parts[1] == _HASH_VERSION:
            _, _, n_text, r_text, p_text, salt_text, digest_text = parts
            actual = _scrypt_digest(
                password,
                _decode(salt_text),
                n=int(n_text),
                r=int(r_text),
                p=int(p_text),
                dklen=len(_decode(digest_text)),
            )
            expected = _decode(digest_text)
        elif len(parts) == 3 and parts[0] == _HASH_SCHEME:
            # Legacy controlled-demo format: scrypt$salt$digest.
            salt = _decode(parts[1])
            expected = _decode(parts[2])
            actual = _scrypt_digest(
                password,
                salt,
                n=_HASH_N,
                r=_HASH_R,
                p=_HASH_P,
                dklen=len(expected),
            )
        else:
            return False
    except (AttributeError, TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def find_user_by_identifier(database: Session, identifier: str) -> User | None:
    """Find a user by exact account phone or normalized email."""
    normalized = identifier.strip()
    if not normalized:
        return None
    phone = normalized if normalized.isdigit() or normalized.startswith("+") else None
    email = normalized.casefold() if "@" in normalized else None
    if phone is None and email is None:
        return None
    clauses = []
    if phone is not None:
        clauses.append(User.phone == phone)
    if email is not None:
        clauses.append(User.email == email)
    return database.scalar(select(User).where(*clauses))
