"""IranKish emulated adapter package (T022, T023)."""

from src.adapters.irankish.adapter import IranKishAdapter
from src.adapters.irankish.routes import router

__all__ = ["IranKishAdapter", "router"]
