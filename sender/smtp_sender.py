from __future__ import annotations

import smtplib
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage

from backend.app.core.config import get_settings


@dataclass(slots=True)
class SendResult:
    provider_message_id: str | None = None


class HourlyRateLimiter:
    """Simple process-local rate limiter.

    For a multi-instance SaaS deployment, replace this with Redis or a database-backed bucket.
    """

    def __init__(self) -> None:
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def check(self, limit: int) -> None:
        now = time.time()
        one_hour_ago = now - 3600
        with self._lock:
            self._timestamps = [stamp for stamp in self._timestamps if stamp > one_hour_ago]
            if len(self._timestamps) >= limit:
                raise RuntimeError("Hourly email rate limit reached")
            self._timestamps.append(now)


rate_limiter = HourlyRateLimiter()


class SmtpOutreachSender:
    """Controlled SMTP sender. It never runs unless EMAIL_SENDING_ENABLED=true."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        missing = [
            name
            for name, value in {
                "SMTP_HOST": self.settings.smtp_host,
                "SMTP_USERNAME": self.settings.smtp_username,
                "SMTP_PASSWORD": self.settings.smtp_password,
                "SMTP_FROM_EMAIL": self.settings.smtp_from_email,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing SMTP settings: {', '.join(missing)}")

        rate_limiter.check(self.settings.email_rate_limit_per_hour)

        message = EmailMessage()
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            response = smtp.send_message(message)

        return SendResult(provider_message_id=str(response) if response else None)

