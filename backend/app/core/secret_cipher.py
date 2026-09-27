"""Authenticated encryption for short-lived OTP secrets."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretCipherError(RuntimeError):
    pass


class SecretCipher:
    def __init__(self, key_material: str) -> None:
        if not key_material:
            raise SecretCipherError("OTP secret encryption is not configured")
        self._key = hashlib.sha256(key_material.encode("utf-8")).digest()

    def encrypt(self, plaintext: str, *, associated_data: bytes) -> str:
        nonce = os.urandom(12)
        ciphertext = AESGCM(self._key).encrypt(
            nonce,
            plaintext.encode("utf-8"),
            associated_data,
        )
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, encoded: str, *, associated_data: bytes) -> str:
        try:
            payload = base64.urlsafe_b64decode(encoded.encode("ascii"))
            if len(payload) < 29:
                raise ValueError
            nonce, ciphertext = payload[:12], payload[12:]
            plaintext = AESGCM(self._key).decrypt(
                nonce,
                ciphertext,
                associated_data,
            )
            return plaintext.decode("utf-8")
        except (ValueError, UnicodeError, InvalidTag) as exc:
            raise SecretCipherError("Stored OTP secret cannot be decrypted") from exc
