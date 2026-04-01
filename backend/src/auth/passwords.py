"""Password hashing utilities."""

import bcrypt

# bcrypt only uses first 72 bytes of password input.
_BCRYPT_MAX_PASSWORD_BYTES = 72


def _normalize_password(password: str) -> bytes:
    """Encode and normalize password bytes for bcrypt compatibility."""
    encoded = password.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_PASSWORD_BYTES:
        return encoded[:_BCRYPT_MAX_PASSWORD_BYTES]
    return encoded


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    normalized = _normalize_password(password)
    return bcrypt.hashpw(normalized, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_normalize_password(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False
