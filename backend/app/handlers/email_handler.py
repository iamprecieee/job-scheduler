import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from loguru import logger


class EmailHandler:
    """Handler for sending emails using aiosmtpd.

    The payload must contain:
    - to: str (recipient email)
    - subject: str (email subject)
    - body: str (email body content)
    """

    async def execute(self, payload: dict[str, Any]) -> None:
        if not all(k in payload for k in ["to", "subject", "body"]):
            raise ValueError("Email payload must contain 'to', 'subject', and 'body'")

        await asyncio.to_thread(self._send_email_sync, payload)

    def _send_email_sync(self, payload: dict[str, Any]) -> None:
        msg = EmailMessage()
        msg.set_content(payload["body"])
        msg["Subject"] = payload["subject"]
        msg["From"] = "noreply@job-scheduler.local"
        msg["To"] = payload["to"]

        try:
            with smtplib.SMTP("127.0.0.1", 8025, timeout=10) as server:
                server.send_message(msg)
            logger.info(f"Email sent successfully to {payload['to']}")
        except Exception as e:
            logger.error(f"Failed to send email to {payload['to']}: {e}")
            raise
