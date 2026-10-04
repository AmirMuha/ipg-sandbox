"""Tests for checkout branding, localization, and auto-submit form (T040)."""

import uuid
from src.checkout.page import render_auto_submit_post_form, render_checkout_page
from src.checkout.styles import BRANDING, get_branding
from src.models import Provider, Transaction


def test_branding_definitions_complete():
    for p in Provider:
        assert p in BRANDING
        b = get_branding(p)
        assert b["name_fa"]
        assert b["name_en"]
        assert b["primary_color"].startswith("#")


def test_checkout_page_fa_and_en():
    tx = Transaction(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        adapter_id=uuid.uuid4(),
        amount_rial=500000,
        authority="12345678",
    )
    html_fa = render_checkout_page(
        tx,
        provider_name="سامان",
        action_url="/saman/checkout/12345678",
        lang="fa",
        provider=Provider.saman,
    )
    assert 'dir="rtl"' in html_fa
    assert "پرداخت الکترونیک سامان" in html_fa
    assert "۵۰۰,۰۰۰" not in html_fa  # formatted with standard commas
    assert "500,000" in html_fa

    html_en = render_checkout_page(
        tx,
        provider_name="Saman",
        action_url="/saman/checkout/12345678",
        lang="en",
        provider=Provider.saman,
    )
    assert 'dir="ltr"' in html_en
    assert "Saman Electronic Payment" in html_en
    assert "Confirm Payment" in html_en


def test_auto_submit_form():
    form_html = render_auto_submit_post_form(
        "https://merchant.example.com/callback",
        {"State": "OK", "RefNum": "12345678"},
    )
    assert 'action="https://merchant.example.com/callback"' in form_html
    assert 'name="State" value="OK"' in form_html
    assert 'name="RefNum" value="12345678"' in form_html
    assert "document.forms[0].submit()" in form_html
