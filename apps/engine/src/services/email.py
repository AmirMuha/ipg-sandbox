"""Email delivery service using standard library smtplib (004-launch-readiness-flows)."""

import email.message
import logging
import os
import smtplib

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, code: str) -> None:
    """Send verification OTP code to recipient via configured SMTP server."""
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port_raw = os.environ.get("SMTP_PORT", "").strip() or "587"
    smtp_port = int(smtp_port_raw)
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    from_email = os.environ.get("SMTP_FROM", "no-reply@ipg-sandbox.local").strip()

    if not smtp_host:
        logger.info(f"Verification OTP generated for {to_email}")
        return

    msg = email.message.EmailMessage()
    msg["Subject"] = "کد تأیید ورود و ثبت‌نام در سندباکس درگاه"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        f"کد تأیید شما برای ثبت‌نام در سندباکس درگاه پرداخت:\n\n"
        f"{code}\n\n"
        f"این کد تا ۵ دقیقه معتبر است."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        if os.environ.get("SMTP_TLS", "true").lower() not in ("false", "0", "no"):
            smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
