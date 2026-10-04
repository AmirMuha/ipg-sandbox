"""Sadad Bank Melli emulated adapter package (T010, T011)."""

from src.adapters.sadad.adapter import SadadAdapter
from src.adapters.sadad.routes import router

__all__ = ["SadadAdapter", "router"]
