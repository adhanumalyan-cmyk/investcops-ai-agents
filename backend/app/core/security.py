"""
Password hashing using bcrypt (modern, no passlib required).
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plaintext password. Never store plaintext."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False