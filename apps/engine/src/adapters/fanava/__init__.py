"""Fanava Card emulated adapter package (T024, T025)."""

from src.adapters.fanava.adapter import FanavaAdapter
from src.adapters.fanava.routes import router

__all__ = ["FanavaAdapter", "router"]
