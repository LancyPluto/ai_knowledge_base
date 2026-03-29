import logging
import smtplib
from email.mime.text import MIMEText
from core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        logger.info("email_fallback_log", extra={"event": "email_fallback_log", "to": to_email, "subject": subject, "body": body})
        return True
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Use SMTP_SSL for port 465 (which is the standard for SSL)
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
        else:
            # Fallback for STARTTLS (usually port 587 or 25)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT or 25) as server:
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
        
        logger.info("email_sent", extra={"event": "email_sent", "to": to_email})
        return True
    except Exception as e:
        logger.exception("email_send_failed", extra={"event": "email_send_failed", "to": to_email})
        return False
