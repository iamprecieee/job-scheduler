import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from loguru import logger

from app.config import settings


class EmailHandler:
    """Handler for sending emails via the local aiosmtpd mock SMTP server.

    Payload keys:
    - to: str      — recipient address
    - subject: str — email subject line
    - body: str    — plain-text body
    """

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        missing = {"to", "subject", "body"} - payload.keys()
        if missing:
            raise ValueError("Email payload missing required keys: {}", missing)

        return await asyncio.to_thread(self._send_email_sync, payload)

    def _send_email_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        msg = EmailMessage()
        msg.set_content(payload["body"])
        msg["Subject"] = payload["subject"]
        msg["From"] = settings.alert_email_from
        msg["To"] = payload["to"]

        # Allow the caller (worker) to handle the exception and decide retry/DLQ;
        # we only raise — no duplicate log here.
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.send_message(msg)

        logger.info("Email sent to {}", payload["to"])

        return {
            "status": "sent",
            "to": payload["to"],
            "subject": payload["subject"],
            "message": msg.as_string(),
        }
