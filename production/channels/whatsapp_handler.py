# whatsapp_handler.py
import os
import httpx
import logging
from typing import Optional
from production.utils.kafka_client import FTEKafkaProducer

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    """Handler for Meta (Facebook) WhatsApp Cloud API."""
    
    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "saasflow_verify_token")
        self.api_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        self.kafka_producer = FTEKafkaProducer()

    async def validate_webhook(self, mode: str, token: str, challenge: str) -> Optional[int]:
        """Validates the Meta webhook verification request (GET)."""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verified successfully!")
            return int(challenge)
        logger.warning("Webhook verification failed.")
        return None

    async def process_webhook(self, data: dict):
        """Processes incoming WhatsApp messages (POST) and pushes to Kafka."""
        try:
            # Meta's JSON structure is deeply nested: entry -> changes -> value -> messages
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if messages:
                msg = messages[0]
                customer_phone = msg.get("from")
                content = msg.get("text", {}).get("body", "")
                
                message_data = {
                    "channel": "whatsapp",
                    "sender": customer_phone,
                    "content": content,
                    "metadata": {
                        "display_name": value.get("contacts", [{}])[0].get("profile", {}).get("name")
                    }
                }
                
                await self.kafka_producer.publish("fte.tickets.incoming", message_data)
                logger.info(f"Published WhatsApp message from {customer_phone} to Kafka.")
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook: {e}")

    async def send_message(self, to_phone: str, text: str):
        """Sends a plain text message via WhatsApp Cloud API."""
        if not self.token:
            raise Exception("WHATSAPP_TOKEN not set in .env")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"body": text}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            result = response.json()
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", response.text)
                logger.error(f"Failed to send WhatsApp message: {error_msg}")
                raise Exception(f"WhatsApp API error ({response.status_code}): {error_msg}")
            logger.info(f"WhatsApp message sent to {to_phone}")
            return result
