"""Visual branding styles, logos, and localized metadata for all 13 gateways (T038)."""

from typing import TypedDict
from src.models import Provider


class GatewayBranding(TypedDict):
    name_fa: str
    name_en: str
    primary_color: str
    secondary_color: str
    logo_svg: str


BRANDING: dict[Provider, GatewayBranding] = {
    Provider.behpardakht: {
        "name_fa": "به‌پرداخت ملت",
        "name_en": "Behpardakht Mellat",
        "primary_color": "#e11d48",
        "secondary_color": "#be123c",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#e11d48" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>',
    },
    Provider.saman: {
        "name_fa": "پرداخت الکترونیک سامان (سپ)",
        "name_en": "Saman Electronic Payment (SEP)",
        "primary_color": "#0284c7",
        "secondary_color": "#0369a1",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#0284c7" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 12l3 3 5-5"/></svg>',
    },
    Provider.sadad: {
        "name_fa": "پرداخت الکترونیک سداد (بانک ملی)",
        "name_en": "Sadad Electronic Payment (Bank Melli)",
        "primary_color": "#059669",
        "secondary_color": "#047857",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#059669" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
    },
    Provider.parsian: {
        "name_fa": "تجارت الکترونیک پارسیان (تاپ)",
        "name_en": "Parsian Electronic Commerce (PEC)",
        "primary_color": "#8b5cf6",
        "secondary_color": "#7c3aed",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#8b5cf6" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
    },
    Provider.pasargad: {
        "name_fa": "پرداخت الکترونیک پاسارگاد (پپ)",
        "name_en": "Pasargad Electronic Payment (PEP)",
        "primary_color": "#d97706",
        "secondary_color": "#b45309",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#d97706" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    },
    Provider.asan_pardakht: {
        "name_fa": "آسان پرداخت (آپ)",
        "name_en": "Asan Pardakht (AP)",
        "primary_color": "#ea580c",
        "secondary_color": "#c2410c",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#ea580c" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    },
    Provider.pardakht_novin: {
        "name_fa": "پرداخت نوین آرین (پی‌ان‌ای)",
        "name_en": "Pardakht Novin Arian (PNA)",
        "primary_color": "#16a34a",
        "secondary_color": "#15803d",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#16a34a" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/></svg>',
    },
    Provider.irankish: {
        "name_fa": "کارت اعتباری ایران‌کیش",
        "name_en": "IranKish Credit Card",
        "primary_color": "#0d9488",
        "secondary_color": "#0f766e",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#0d9488" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    },
    Provider.fanava: {
        "name_fa": "فن‌آوا کارت",
        "name_en": "Fanava Card",
        "primary_color": "#4f46e5",
        "secondary_color": "#4338ca",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#4f46e5" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><line x1="2" y1="10" x2="22" y2="10"/></svg>',
    },
    Provider.sarmayeh: {
        "name_fa": "پرداخت الکترونیک سرمایه",
        "name_en": "Sarmayeh Payment",
        "primary_color": "#65a30d",
        "secondary_color": "#4d7c0f",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#65a30d" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v12M15 9.5a3.5 3.5 0 0 0-5 0 3.5 3.5 0 0 0 0 5 3.5 3.5 0 0 0 5 0"/></svg>',
    },
    Provider.sizpay: {
        "name_fa": "سیزپی (پرداخت‌یار)",
        "name_en": "SizPay Facilitator",
        "primary_color": "#2563eb",
        "secondary_color": "#1d4ed8",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#2563eb" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 16l4-4-4-4"/></svg>',
    },
    Provider.zarinpal: {
        "name_fa": "زرین‌پال",
        "name_en": "ZarinPal",
        "primary_color": "#eab308",
        "secondary_color": "#ca8a04",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#eab308" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>',
    },
    Provider.idpay: {
        "name_fa": "آیدی‌پی",
        "name_en": "IDPay",
        "primary_color": "#06b6d4",
        "secondary_color": "#0891b2",
        "logo_svg": '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#06b6d4" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/></svg>',
    },
}


def get_branding(provider: Provider) -> GatewayBranding:
    """Return styling and localization metadata for `provider`."""
    return BRANDING.get(
        provider,
        {
            "name_fa": str(provider.value),
            "name_en": str(provider.value).title(),
            "primary_color": "#3b82f6",
            "secondary_color": "#2563eb",
            "logo_svg": "",
        },
    )
