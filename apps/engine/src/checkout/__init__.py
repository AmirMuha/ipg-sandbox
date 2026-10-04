"""Hosted checkout page rendering (T024, T038)."""

from src.checkout.page import render_auto_submit_post_form, render_checkout_page
from src.checkout.styles import BRANDING, get_branding

__all__ = ["render_checkout_page", "render_auto_submit_post_form", "get_branding", "BRANDING"]
