"""Hosted checkout page template and renderer (T024) — contracts §5, FR-012.

Never collects card data (no card number, cvv, expiry, pin inputs).
Server-rendered HTML string with native form POST, works offline without CDN.
RTL Persian default, LTR English supported via ?lang=en.
"""

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import Transaction


def render_checkout_page(
    tx: "Transaction",
    *,
    provider_name: str,
    action_url: str,
    lang: str = "fa",
) -> str:
    """Render hosted payment simulation page for `tx`."""
    is_fa = lang.lower() == "fa"
    direction = "rtl" if is_fa else "ltr"
    html_lang = "fa" if is_fa else "en"

    title = "درگاه پرداخت آزمایشی (سندباکس)" if is_fa else "IPG Sandbox Checkout"
    provider_title = f"درگاه {provider_name}" if is_fa else f"{provider_name} Gateway"
    amount_label = "مبلغ قابل پرداخت:" if is_fa else "Amount to Pay:"
    authority_label = "شناسه پرداخت / Authority:" if is_fa else "Authority / Ref ID:"
    reference_label = "شناسه سفارش:" if is_fa else "Order Reference:"
    currency_label = "ریال" if is_fa else "IRR"
    notice = (
        "این صفحه صرفاً جهت شبیه‌سازی درگاه پرداخت بوده و هیچ اطلاعات بانکی دریافت نمی‌شود."
        if is_fa
        else "This is a simulated sandbox checkout. No real money or card details are handled."
    )

    btn_confirm = "تایید و تکمیل پرداخت" if is_fa else "Confirm Payment"
    btn_fail = "انصراف و لغو پرداخت" if is_fa else "Cancel Payment"
    btn_abandon = "بستن / رها کردن پنجره" if is_fa else "Abandon Checkout"

    formatted_amount = f"{tx.amount_rial:,}"
    safe_authority = html.escape(str(tx.authority or ""))
    safe_reference = html.escape(str(tx.app_reference or "—"))
    safe_action = html.escape(action_url)

    return f"""<!DOCTYPE html>
<html lang="{html_lang}" dir="{direction}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --warning: #eab308;
            --warning-hover: #ca8a04;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            min-height: 100vh;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            width: 100%;
            max-width: 440px;
            padding: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1rem;
        }}
        .header h1 {{ font-size: 1.25rem; font-weight: 600; }}
        .header p {{ font-size: 0.875rem; color: var(--text-muted); margin-top: 0.25rem; }}
        .notice {{
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 0.8125rem;
            color: #93c5fd;
            margin-bottom: 1.25rem;
            line-height: 1.4;
        }}
        .row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
            font-size: 0.875rem;
        }}
        .row .label {{ color: var(--text-muted); }}
        .row .value {{ font-weight: 500; font-family: monospace; }}
        .amount-row {{
            margin: 1rem 0 1.5rem 0;
            padding: 0.75rem;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .amount-row .amount {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #60a5fa;
        }}
        .actions {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }}
        button {{
            cursor: pointer;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 0.9375rem;
            font-weight: 600;
            transition: background 0.15s ease;
        }}
        .btn-confirm {{ background: var(--primary); color: white; }}
        .btn-confirm:hover {{ background: var(--primary-hover); }}
        .btn-fail {{ background: var(--danger); color: white; }}
        .btn-fail:hover {{ background: var(--danger-hover); }}
        .btn-abandon {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
        }}
        .btn-abandon:hover {{ background: rgba(255,255,255,0.05); color: var(--text); }}
        .lang-switch {{
            margin-top: 1.25rem;
            text-align: center;
            font-size: 0.8125rem;
        }}
        .lang-switch a {{ color: var(--text-muted); text-decoration: none; }}
        .lang-switch a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>{title}</h1>
            <p>{provider_title}</p>
        </div>
        <div class="notice">
            {notice}
        </div>
        <div class="details">
            <div class="row">
                <span class="label">{authority_label}</span>
                <span class="value">{safe_authority}</span>
            </div>
            <div class="row">
                <span class="label">{reference_label}</span>
                <span class="value">{safe_reference}</span>
            </div>
            <div class="amount-row">
                <span>{amount_label}</span>
                <span class="amount">{formatted_amount} {currency_label}</span>
            </div>
        </div>
        <form method="post" action="{safe_action}" class="actions">
            <button type="submit" name="action" value="confirm"
                    class="btn-confirm">{btn_confirm}</button>
            <button type="submit" name="action" value="fail"
                    class="btn-fail">{btn_fail}</button>
            <button type="submit" name="action" value="abandon"
                    class="btn-abandon">{btn_abandon}</button>
        </form>
        <div class="lang-switch">
            <a href="?lang={"en" if is_fa else "fa"}">{"English" if is_fa else "فارسی"}</a>
        </div>
    </div>
</body>
</html>"""
