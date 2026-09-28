"""IDPay emulated adapter package (T022)."""

from src.adapters.idpay.adapter import IDPayAdapter
from src.adapters.idpay.routes import router

__all__ = ["IDPayAdapter", "router"]
