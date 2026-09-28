"""Unit tests for hosted checkout page rendering (T024, FR-012)."""

from unittest.mock import MagicMock

from src.checkout.page import render_checkout_page


def test_checkout_page_fr012_and_rtl():
    tx = MagicMock()
    tx.amount_rial = 500000
    tx.authority = "A-test-123"
    tx.app_reference = "order-99"

    # Default FA RTL
    html_fa = render_checkout_page(
        tx,
        provider_name="Zarinpal",
        action_url="/zarinpal/checkout/A-test-123",
    )
    assert 'dir="rtl"' in html_fa
    assert 'lang="fa"' in html_fa
    assert "500,000" in html_fa
    assert "A-test-123" in html_fa
    assert 'action="/zarinpal/checkout/A-test-123"' in html_fa
    assert '<button type="submit" name="action" value="confirm"' in html_fa
    assert '<button type="submit" name="action" value="fail"' in html_fa
    assert '<button type="submit" name="action" value="abandon"' in html_fa

    # FR-012: Never collects card data
    lower_fa = html_fa.lower()
    assert "<input" not in lower_fa
    assert "card_number" not in lower_fa
    assert "card_pan" not in lower_fa
    assert "cvv" not in lower_fa
    assert "pin" not in lower_fa

    # English LTR
    html_en = render_checkout_page(
        tx,
        provider_name="Zarinpal",
        action_url="/zarinpal/checkout/A-test-123",
        lang="en",
    )
    assert 'dir="ltr"' in html_en
    assert 'lang="en"' in html_en
    assert "Confirm Payment" in html_en
    assert "<input" not in html_en.lower()
