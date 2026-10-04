"""Bank Sarmayeh emulated adapter package (T026, T027)."""

from src.adapters.sarmayeh.adapter import SarmayehAdapter
from src.adapters.sarmayeh.routes import router

__all__ = ["SarmayehAdapter", "router"]
