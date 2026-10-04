"""Permissive cryptographic signature verification (FR-013, research R5).

Three gateways specify cryptographic signatures on inbound requests:
  - Pasargad PEP: RSA PKCS#1 v1.5 with SHA1 on `#`-delimited invoice data (ipg-pasargad.pdf:107)
  - Sadad Melli:  `SignData` on PaymentRequest and Verify endpoints
  - IranKish:     HMAC token on the WCF TToken request

Permissive mode (the default):
  If the adapter config contains no signing key, inbound signatures are accepted unconditionally.
  This removes the onboarding friction of generating certificates just to run local sandbox tests.

Strict mode:
  When an adapter configuration provides a public key / secret in `credentials["public_key"]`
  or `credentials["sign_key"]`, mathematical verification is enforced via the `cryptography` library.
"""

import base64
import hmac
import logging
from hashlib import sha1, sha256

logger = logging.getLogger(__name__)


def verify_rsa(
    public_pem: str | None,
    signature_b64: str,
    payload: str | bytes,
    *,
    hash_algo: str = "sha1",
) -> bool:
    """Verify an RSA PKCS#1 v1.5 signature.

    Returns True if `public_pem` is None or empty (permissive mode).
    """
    if not public_pem or not public_pem.strip():
        return True  # Permissive mode

    if not signature_b64:
        return False

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        sig_bytes = base64.b64decode(signature_b64)
        data_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload

        key = load_pem_public_key(public_pem.encode("utf-8") if isinstance(public_pem, str) else public_pem)
        hasher = hashes.SHA256() if hash_algo.lower() == "sha256" else hashes.SHA1()

        key.verify(sig_bytes, data_bytes, padding.PKCS1v15(), hasher)
        return True
    except Exception as exc:
        logger.warning("RSA signature verification failed: %s", exc)
        return False


def verify_hmac(
    secret: str | None,
    signature_hex_or_b64: str,
    payload: str | bytes,
    *,
    hash_algo: str = "sha256",
) -> bool:
    """Verify an HMAC digest.

    Returns True if `secret` is None or empty (permissive mode).
    """
    if not secret or not secret.strip():
        return True  # Permissive mode

    if not signature_hex_or_b64:
        return False

    try:
        data_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        secret_bytes = secret.encode("utf-8")
        hasher = sha256 if hash_algo.lower() == "sha256" else sha1

        expected = hmac.new(secret_bytes, data_bytes, hasher).digest()

        # Try hex first, fallback to base64
        try:
            actual = bytes.fromhex(signature_hex_or_b64)
        except ValueError:
            actual = base64.b64decode(signature_hex_or_b64)

        return hmac.compare_digest(actual, expected)
    except Exception as exc:
        logger.warning("HMAC signature verification failed: %s", exc)
        return False
