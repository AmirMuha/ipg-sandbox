"""Unit tests for metadata and crypto helpers (T005)."""

import uuid

import pytest

from src.adapters.crypto import verify_hmac, verify_rsa
from src.adapters.metadata import BANK_BINS, card_metadata, masked_pan, rrn, trace_no
from src.models import Provider, Transaction


@pytest.fixture
def sample_tx() -> Transaction:
    tx = Transaction(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        project_id=uuid.uuid4(),
        adapter_id=uuid.uuid4(),
        amount_rial=500000,
        authority="TEST-AUTH",
    )
    return tx


def test_metadata_pan_format(sample_tx: Transaction):
    pan = masked_pan(Provider.sadad, sample_tx)
    assert pan.startswith("603799")
    assert "******" in pan
    assert len(pan) == 16


def test_metadata_rrn_and_trace(sample_tx: Transaction):
    r = rrn(sample_tx)
    assert len(r) == 12
    assert r.isdigit()

    t = trace_no(sample_tx)
    assert len(t) == 6
    assert t.isdigit()


def test_metadata_card_metadata_bundle(sample_tx: Transaction):
    bundle = card_metadata(Provider.saman, sample_tx)
    assert bundle["card_pan"].startswith(BANK_BINS[Provider.saman])
    assert len(bundle["rrn"]) == 12
    assert len(bundle["trace_no"]) == 6


def test_crypto_permissive_mode():
    # Permissive by default when public_key/secret is None or empty
    assert verify_rsa(None, "dummy_sig", "data") is True
    assert verify_rsa("", "dummy_sig", "data") is True
    assert verify_hmac(None, "dummy_sig", "data") is True
    assert verify_hmac("", "dummy_sig", "data") is True


def test_crypto_hmac_strict():
    secret = "my_secret_key"
    payload = "invoice_data"
    import hmac
    from hashlib import sha256

    valid_sig = hmac.new(secret.encode(), payload.encode(), sha256).hexdigest()
    assert verify_hmac(secret, valid_sig, payload, hash_algo="sha256") is True
    assert verify_hmac(secret, "bad_sig", payload, hash_algo="sha256") is False
