# message_processor.py
import asyncio
import json
import logging
from datetime import datetime
from production.utils.kafka_client import FTEKafkaConsumer, FTEKafkaProducer
from production.agent.customer_success_agent import (
    customer_success_agent, get_run_config, get_next_api_key, external_client
)
from agents import Runner
from production.agent.tools import get_db_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 20  # seconds (Gemini free tier resets per-minute)

class UnifiedMessageProcessor:
    """Consumes messages from Kafka and runs the Digital FTE Agent."""
    
    def __init__(self):
        self.producer = None
        self.consumer = None

    async def start(self):
        self.producer = FTEKafkaProducer()
        await self.producer.start()
        
        self.consumer = FTEKafkaConsumer(
            topics=["fte.tickets.incoming"],
            group_id="fte-message-processor"
        )
        await self.consumer.start()
        logger.info("Message processor started, listening for tickets...")
        await self.consumer.consume(self.process_message)

    async def process_message(self, topic: str, message: dict):
        """Logic to process a single message from any channel."""
        start_time = datetime.now()
        try:
            channel = message.get("channel", "web_form")
            content = message.get("content") or message.get("message", "")
            customer_email = message.get("email") or message.get("customer_email")
            customer_phone = message.get("sender")  # WhatsApp phone number
            identifier = customer_email or customer_phone

            logger.info(f"Processing message from {channel}: {identifier}")

            # 1. Resolve Customer ID from DB (with cross-channel identity matching)
            customer_id = await self.resolve_customer(
                customer_email, message.get("name"),
                phone=customer_phone, channel=channel
            )

            # 2. Get Run Config
            config = get_run_config()

            # 3. Run Agent (OpenAI SDK + Gemini) with retry on rate limit
            enriched_content = f"[CONTEXT: identifier={identifier}, channel={channel}] User Message: {content}"

            result = None
            for attempt in range(MAX_RETRIES + 1):
                try:
                    result = await Runner.run(
                        customer_success_agent,
                        enriched_content,
                        context={
                            "customer_id": identifier,
                            "channel": channel
                        },
                        run_config=config
                    )
                    break  # Success, exit retry loop
                except Exception as run_err:
                    err_str = str(run_err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate" in err_str.lower():
                        if attempt < MAX_RETRIES:
                            # Rotate to next API key and retry
                            new_key = get_next_api_key()
                            external_client.api_key = new_key
                            delay = RETRY_BASE_DELAY * (attempt + 1)
                            logger.warning(
                                f"[RATE LIMIT] 429 hit on attempt {attempt+1}/{MAX_RETRIES+1}. "
                                f"Rotating API key and retrying in {delay}s..."
                            )
                            await asyncio.sleep(delay)
                        else:
                            raise  # All retries exhausted
                    else:
                        raise  # Non-rate-limit error, don't retry

            if result is None:
                raise Exception("Agent run returned no result after retries")

            # --- Robust Response Extraction ---
            # Try every possible way to find the agent's actual message
            final_msg = ""

            # 1. Try final_output (skip if it's just a tool confirmation)
            if hasattr(result, 'final_output') and result.final_output:
                output = str(result.final_output)
                if "Response delivered" not in output:
                    final_msg = output

            # 2. Search through all messages for send_response tool call args
            if not final_msg:
                all_msgs = []
                if hasattr(result, 'raw_responses'):
                    all_msgs = result.raw_responses
                if hasattr(result, 'messages'):
                    all_msgs = result.messages
                elif hasattr(result, 'history'):
                    all_msgs = result.history

                for m in reversed(all_msgs):
                    # Check tool_calls attribute (OpenAI SDK format)
                    if hasattr(m, 'tool_calls') and m.tool_calls:
                        for tc in m.tool_calls:
                            fn = getattr(tc, 'function', tc)
                            fn_name = getattr(fn, 'name', '')
                            fn_args = getattr(fn, 'arguments', '{}')
                            if fn_name == "send_response":
                                try:
                                    args = json.loads(fn_args) if isinstance(fn_args, str) else fn_args
                                    msg = args.get("message", "") or args.get("input", {}).get("message", "")
                                    if msg:
                                        final_msg = msg
                                        break
                                except: pass
                    # Check content for structured output
                    if not final_msg and hasattr(m, 'content') and m.content:
                        content = m.content
                        # content can be a list of parts
                        if isinstance(content, list):
                            for part in content:
                                if hasattr(part, 'text') and part.text:
                                    final_msg = part.text
                                    break
                        elif isinstance(content, str) and "Response delivered" not in content:
                            role = getattr(m, 'role', '')
                            if role == 'assistant':
                                final_msg = content
                    if final_msg: break

            # 3. Last resort: check new_items on result
            if not final_msg and hasattr(result, 'new_items'):
                for item in reversed(result.new_items):
                    if hasattr(item, 'raw_item'):
                        raw = item.raw_item
                        if hasattr(raw, 'tool_calls') and raw.tool_calls:
                            for tc in raw.tool_calls:
                                fn = getattr(tc, 'function', tc)
                                if getattr(fn, 'name', '') == 'send_response':
                                    try:
                                        args = json.loads(getattr(fn, 'arguments', '{}'))
                                        msg = args.get("message", "") or args.get("input", {}).get("message", "")
                                        if msg:
                                            final_msg = msg
                                            break
                                    except: pass
                    if final_msg: break

            # Check if agent actually called send_response (check ALL sources)
            agent_called_send = False

            # Check new_items
            for item in getattr(result, 'new_items', []):
                raw = getattr(item, 'raw_item', None)
                if raw and hasattr(raw, 'tool_calls') and raw.tool_calls:
                    for tc in raw.tool_calls:
                        fn = getattr(tc, 'function', tc)
                        if getattr(fn, 'name', '') == 'send_response':
                            agent_called_send = True
                            break

            # Also check messages / raw_responses for tool calls
            if not agent_called_send:
                for src in ['messages', 'raw_responses', 'history']:
                    for m in getattr(result, src, []):
                        if hasattr(m, 'tool_calls') and m.tool_calls:
                            for tc in m.tool_calls:
                                fn = getattr(tc, 'function', tc)
                                if getattr(fn, 'name', '') == 'send_response':
                                    agent_called_send = True
                                    break
                        if agent_called_send:
                            break
                    if agent_called_send:
                        break

            # Also check final_output — "Response delivered" means send_response ran
            if not agent_called_send and hasattr(result, 'final_output'):
                out = str(result.final_output)
                if "Response delivered" in out or "response noted" in out.lower():
                    agent_called_send = True

            print("\n" + "="*50)
            print(f"AGENT RESPONSE FOR: {customer_email}")
            print(f"FINAL OUTPUT: {final_msg if final_msg else '[No text found in response]'}")
            print(f"SEND_RESPONSE CALLED: {agent_called_send}")
            print("="*50 + "\n")

            # 4. FALLBACK DELIVERY — if agent didn't call send_response, deliver ourselves
            if final_msg and not agent_called_send:
                logger.info(f"[FALLBACK] Agent didn't call send_response. Delivering {channel} message directly.")
                await self._fallback_deliver(channel, customer_email, customer_phone, final_msg)

            # 5. Extract token usage from agent result
            tokens_used = 0
            if hasattr(result, 'raw_responses'):
                for resp in result.raw_responses:
                    if hasattr(resp, 'usage') and resp.usage:
                        tokens_used += getattr(resp.usage, 'total_tokens', 0)

            # 6. Log Metrics
            duration = (datetime.now() - start_time).total_seconds() * 1000
            await self.producer.publish("fte.metrics", {
                "event_type": "message_processed",
                "channel": channel,
                "latency_ms": duration,
                "tokens_used": tokens_used,
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Send apologetic response to customer via email/whatsapp AND metrics topic
            try:
                apology = (
                    "Dear Customer,\n\n"
                    "We sincerely apologize for the inconvenience. Our system encountered "
                    "a temporary issue processing your request. A human agent has been notified "
                    "and will follow up with you shortly.\n\n"
                    "Thank you for your patience.\n\n"
                    "Sincerely,\nThe SaaSFlow Support Team"
                )
                err_channel = message.get("channel", "unknown")
                err_email = message.get("email") or message.get("customer_email")
                err_phone = message.get("sender")

                # Actually deliver the apology to the customer
                await self._fallback_deliver(err_channel, err_email, err_phone, apology)

                await self.producer.publish("fte.metrics", {
                    "event_type": "error_response",
                    "channel": err_channel,
                    "customer_email": err_email or "unknown",
                    "apology_message": apology,
                    "error": str(e),
                    "status": "error"
                })
            except Exception as inner_e:
                logger.error(f"Failed to send error apology: {inner_e}")

    async def _fallback_deliver(self, channel: str, email: str, phone: str, message: str):
        """Fallback delivery when agent doesn't call send_response tool."""
        try:
            if channel == "whatsapp" and phone:
                from production.channels.whatsapp_handler import WhatsAppHandler
                wa = WhatsAppHandler()
                resp = await wa.send_message(phone, message)
                print(f"[FALLBACK] WhatsApp sent to {phone}: {resp}")

            elif email:
                # For email, web_form, or any channel — send email if we have one
                from production.channels.gmail_handler import GmailHandler
                gmail = GmailHandler()
                resp = await gmail.send_email_smtp(email, "SaaSFlow Support Response", message)
                print(f"[FALLBACK] Email sent to {email}: {resp}")

            else:
                logger.info(f"[FALLBACK] No delivery target (channel={channel}, email={email}, phone={phone})")

        except Exception as e:
            logger.error(f"[FALLBACK] Delivery failed for {channel}: {e}")

    async def resolve_customer(self, email: str, name: str = None, phone: str = None, channel: str = "web_form") -> str:
        """Finds or creates a customer in the PostgreSQL DB with cross-channel identity matching."""
        from production.agent.tools import register_customer_identifier, resolve_customer_by_identifier
        conn = await get_db_conn()
        try:
            customer_id = None

            # 1. Try cross-channel identity matching
            if email:
                customer_id = await resolve_customer_by_identifier(conn, "email", email)
            if not customer_id and phone:
                customer_id = await resolve_customer_by_identifier(conn, "whatsapp", phone)

            # 2. Fallback to direct email lookup
            if not customer_id and email:
                row = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", email)
                if row:
                    customer_id = row['id']

            # 3. Create new customer if not found
            if not customer_id:
                customer_id = await conn.fetchval(
                    "INSERT INTO customers (email, name, phone) VALUES ($1, $2, $3) RETURNING id",
                    email, name or "Customer", phone
                )

            # 4. Register identifiers for future cross-channel matching
            if email:
                await register_customer_identifier(conn, customer_id, "email", email)
            if phone:
                await register_customer_identifier(conn, customer_id, "whatsapp", phone)

            return str(customer_id)
        finally:
            await conn.close()

if __name__ == "__main__":
    processor = UnifiedMessageProcessor()
    asyncio.run(processor.start())
