"""Authentication service: password hashing and token management (004-launch-readiness-flows).

Uses Python 3.12 stdlib hashlib.scrypt, secrets, and hmac only — zero external crypto packages.
"""

import hashlib
import hmac
import os
import secrets

SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 64 * 1024 * 1024


def hash_password(password: str) -> str:
    """Hash password using scrypt with a secure 16-byte random salt."""
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored scrypt hash in constant time."""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])

        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=SCRYPT_MAXMEM,
        )
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate a 32-byte cryptographically secure random session token."""
    return secrets.token_hex(32)


def hash_session_token(token: str) -> str:
    """Compute SHA-256 digest of session token for safe persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
