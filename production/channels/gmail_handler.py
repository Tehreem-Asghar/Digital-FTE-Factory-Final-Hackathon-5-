# gmail_handler.py
import os
import base64
import logging
import smtplib
import aiosmtplib
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from production.utils.kafka_client import FTEKafkaProducer

logger = logging.getLogger(__name__)


class GmailHandler:
    """Handler for Gmail API via Google Cloud Pub/Sub notifications + SMTP delivery."""

    def __init__(self):
        self.client_id = os.getenv("GMAIL_CLIENT_ID")
        self.project_id = os.getenv("GOOGLE_PROJECT_ID", "saasflow-fte")
        self.topic_name = os.getenv("GMAIL_PUBSUB_TOPIC", f"projects/{self.project_id}/topics/gmail-notifications")
        # SMTP config for sending emails
        self.smtp_email = os.getenv("SMTP_EMAIL")  # e.g. your-gmail@gmail.com
        self.smtp_password = os.getenv("SMTP_APP_PASSWORD")  # Gmail App Password (16 chars)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.kafka_producer = FTEKafkaProducer()

    async def process_pubsub_notification(self, data: dict) -> Dict[str, Any]:
        """
        Processes a Gmail Pub/Sub push notification.

        Google Pub/Sub sends:
        {
            "message": {
                "data": "<base64-encoded>",  // contains {"emailAddress": "...", "historyId": "..."}
                "messageId": "...",
                "publishTime": "..."
            },
            "subscription": "projects/.../subscriptions/..."
        }
        """
        try:
            message = data.get("message", {})
            encoded_data = message.get("data", "")

            if not encoded_data:
                logger.warning("Empty Pub/Sub notification received.")
                return {"status": "ignored", "reason": "empty_data"}

            # Decode the base64 Pub/Sub payload
            import json
            decoded = base64.b64decode(encoded_data).decode("utf-8")
            notification = json.loads(decoded)

            email_address = notification.get("emailAddress", "unknown")
            history_id = notification.get("historyId")

            logger.info(f"Gmail notification for {email_address}, historyId={history_id}")

            # Build the message payload for Kafka
            message_data = {
                "channel": "email",
                "email": email_address,
                "content": f"[Gmail notification] New email activity detected for {email_address}",
                "metadata": {
                    "history_id": history_id,
                    "source": "gmail_pubsub",
                    "pubsub_message_id": message.get("messageId"),
                    "publish_time": message.get("publishTime"),
                },
            }

            await self.kafka_producer.publish("fte.tickets.incoming", message_data)
            logger.info(f"Published Gmail notification for {email_address} to Kafka.")

            return {"status": "ok", "email": email_address}

        except Exception as e:
            logger.error(f"Error processing Gmail Pub/Sub notification: {e}")
            return {"status": "error", "detail": str(e)}

    async def parse_email_content(self, raw_email: dict) -> Dict[str, str]:
        """
        Parses a Gmail API message resource into structured fields.

        Expects the output from Gmail API:
        GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}
        """
        headers = {h["name"]: h["value"] for h in raw_email.get("payload", {}).get("headers", [])}

        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "unknown")
        to = headers.get("To", "unknown")

        # Extract body - try plain text first, then html
        body = ""
        payload = raw_email.get("payload", {})

        if payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break

        return {
            "subject": subject,
            "from": sender,
            "to": to,
            "body": body,
            "message_id": raw_email.get("id", ""),
            "thread_id": raw_email.get("threadId", ""),
        }

    async def send_email(self, to_email: str, subject: str, body: str, access_token: str) -> dict:
        """
        Sends an email reply via Gmail API.
        Requires a valid OAuth2 access token.
        """
        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject
        message["from"] = "support@saasflow.io"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers=headers,
                json={"raw": raw_message},
            )

            if response.status_code == 200:
                logger.info(f"Email sent to {to_email}")
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")

            return response.json()

    async def send_email_smtp(self, to_email: str, subject: str, body: str) -> dict:
        """
        Send email via SMTP (Gmail App Password) — no OAuth needed.
        Requires SMTP_EMAIL and SMTP_APP_PASSWORD in .env
        """
        if not self.smtp_email or not self.smtp_password:
            logger.warning("SMTP credentials not configured (SMTP_EMAIL / SMTP_APP_PASSWORD missing)")
            return {"status": "skipped", "reason": "SMTP not configured"}

        msg = MIMEMultipart("alternative")
        msg["From"] = f"SaaSFlow Support <{self.smtp_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject or "SaaSFlow Support Response"

        # Plain text version
        msg.attach(MIMEText(body, "plain"))

        # Simple HTML version
        html_body = body.replace("\n", "<br>")
        html = f"""<div style="font-family:Arial,sans-serif;font-size:14px;color:#333;max-width:600px;">
            {html_body}
            <hr style="margin-top:20px;border:none;border-top:1px solid #e0e0e0;">
            <p style="font-size:12px;color:#888;">Powered by SaaSFlow Digital FTE</p>
        </div>"""
        msg.attach(MIMEText(html, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_email,
                password=self.smtp_password,
            )
            logger.info(f"[EMAIL] Sent to {to_email} via SMTP")
            return {"status": "sent", "to": to_email}
        except Exception as e:
            logger.error(f"[EMAIL] SMTP send failed: {e}")
            raise Exception(f"SMTP delivery failed: {e}")
