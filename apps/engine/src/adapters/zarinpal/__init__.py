"""Zarinpal emulated adapter package (T021)."""

from src.adapters.zarinpal.adapter import ZarinpalAdapter
from src.adapters.zarinpal.routes import router

__all__ = ["ZarinpalAdapter", "router"]
