"""
Async email gateway via aiosmtplib.
Graceful no-op when not configured.
"""
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER


def is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


async def send_email(
    to: str,
    subject: str,
    body_html: str,
    from_addr: Optional[str] = None,
) -> bool:
    """
    Send an HTML email asynchronously.
    Returns True on success, False otherwise.
    """
    if not is_configured():
        logger.debug("Email gateway not configured, skipping")
        return False

    try:
        import aiosmtplib
    except ImportError:
        logger.warning("aiosmtplib not installed, email skipped")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr or SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=SMTP_PORT == 465,
            start_tls=SMTP_PORT == 587,
            timeout=15,
        )
        logger.info(f"Email sent: to={to}, subject={subject[:30]}")
        return True
    except Exception as e:
        logger.warning(f"Email send failed: {e}")
        return False
