"""Encryption helpers for sensitive secrets."""
from base64 import urlsafe_b64encode
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = urlsafe_b64encode(digest).decode()
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid encryption key configured") from exc


def encrypt_string(value: str) -> str:
    """Encrypt a string payload."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_string(token: str) -> str:
    """Decrypt a string payload."""
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt secret") from exc
