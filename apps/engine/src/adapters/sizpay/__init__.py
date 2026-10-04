"""SizPay emulated adapter package (T030, T031)."""

from src.adapters.sizpay.adapter import SizpayAdapter
from src.adapters.sizpay.routes import router

__all__ = ["SizpayAdapter", "router"]
