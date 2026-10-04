"""Deterministic cardholder metadata generation (FR-014, research R4, data-model §3).

Real Iranian reconciliation software parses and logs masked card PANs, 12-digit Retrieval
Reference Numbers (RRN), and 6-digit System Trace Audit Numbers (TraceNo). Generating them
deterministically from `tx.id` makes test assertions repeatable while exercising the exact
data shapes merchant apps expect.
"""

from src.models import Provider, Transaction

#: Official bank BIN prefixes (6 digits) recognized across Shaparak.
#: Where a gateway doc names a specific prefix, that takes precedence.
BANK_BINS: dict[Provider, str] = {
    Provider.sadad: "603799",          # Bank Melli
    Provider.behpardakht: "610433",     # Bank Mellat
    Provider.saman: "621986",           # Saman Bank
    Provider.parsian: "622106",         # Parsian Bank
    Provider.pasargad: "502229",        # Pasargad Bank
    Provider.irankish: "585983",        # Tejarat Bank
    Provider.pardakht_novin: "627412",  # Eghtesad Novin Bank
    Provider.sarmayeh: "639607",        # Sarmayeh Bank
    Provider.asan_pardakht: "603770",   # Keshavarzi Bank
    # Default to Pasargad BIN for payment facilitators (ZarinPal, IDPay, SizPay, Fanava)
    Provider.zarinpal: "502229",
    Provider.idpay: "502229",
    Provider.sizpay: "502229",
    Provider.fanava: "502229",
}

DEFAULT_BIN = "502229"


def _deterministic_seed(tx: Transaction) -> int:
    """Stable integer seed derived from `tx.id`."""
    return abs(tx.id.int if tx.id is not None else 12345)


def masked_pan(provider: Provider, tx: Transaction) -> str:
    """16-digit masked card PAN with official Iranian bank BIN: `603799******1234`."""
    bin_prefix = BANK_BINS.get(provider, DEFAULT_BIN)
    last4 = _deterministic_seed(tx) % 10000
    return f"{bin_prefix}******{last4:04d}"


def rrn(tx: Transaction) -> str:
    """12-digit numeric Retrieval Reference Number (RRN)."""
    # 8-digit date-like prefix + 4-digit tx counter
    seed = _deterministic_seed(tx)
    return f"20261003{seed % 10000:04d}"


def trace_no(tx: Transaction) -> str:
    """6-digit numeric System Audit Trace Number (TraceNo)."""
    return f"{_deterministic_seed(tx) % 1000000:06d}"


def card_metadata(provider: Provider, tx: Transaction) -> dict[str, str]:
    """Single call returning all cardholder metadata for a transaction."""
    return {
        "card_pan": masked_pan(provider, tx),
        "rrn": rrn(tx),
        "trace_no": trace_no(tx),
    }
