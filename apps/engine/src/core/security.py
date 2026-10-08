import hashlib
import secrets
import string

API_KEY_PREFIX = "ipg_key_"
API_KEY_LENGTH = 32

def generate_api_key() -> str:
    """Generate a new secure API key with the required prefix."""
    random_part = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(API_KEY_LENGTH)
    )
    return f"{API_KEY_PREFIX}{random_part}"

def hash_api_key(api_key: str) -> str:
    """Compute the SHA-256 hash of an API key for secure database storage."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
