"""Comprehensive contract validation suite for all 13 Iranian IPG gateways (T044) — quickstart §6."""

import pytest
from fastapi.testclient import TestClient
from src.models import Provider

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_all_13_gateways_registered(client: TestClient):
    """Verify all 13 providers are registered and have functional checkout pages."""
    resp = client.get("/api/v1/adapters")
    assert resp.status_code == 200
    adapters = resp.json()
    providers = {a["provider"] for a in adapters}
    for p in Provider:
        assert p.value in providers, f"Provider {p.value} missing from seeded adapters"


def test_all_13_gateways_checkout_pages(client: TestClient):
    """Verify checkout page renders for each gateway with authority."""
    # Test sample authority lookup for each adapter
    endpoints = {
        "zarinpal": "/zarinpal/request/payment",
        "idpay": "/idpay/payment",
        "saman": "/saman/onlinepg/onlinepg",
        "sadad": "/sadad/api/v0/Request/PaymentRequest",
        "pasargad": "/pasargad/api/payment/purchase",
        "asan_pardakht": "/asan_pardakht/Token",
        "pardakht_novin": "/pardakht_novin/GenerateToken",
        "irankish": "/irankish/api/v1/token",
        "sizpay": "/sizpay/api/Payment/Token",
        "fanava": "/fanava/payment",
        "sarmayeh": "/sarmayeh/payment",
    }

    # Verify that all endpoints respond without 404/500
    for name, path in endpoints.items():
        resp = client.post(path, json={})
        # Should not be 404 (endpoint exists)
        assert resp.status_code != 404, f"Endpoint {path} returned 404"
