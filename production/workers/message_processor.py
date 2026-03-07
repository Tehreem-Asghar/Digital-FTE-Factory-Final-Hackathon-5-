# message_processor.py
import asyncio
import json
import logging
from datetime import datetime
from production.utils.kafka_client import FTEKafkaConsumer, FTEKafkaProducer
from production.agent.customer_success_agent import (
    customer_success_agent, get_run_config, rotate_client
)
from agents import Runner
from production.agent.tools import get_db_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_BASE_DELAY = 60  # seconds (Wait full minute for quota reset)

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

            from production.agent.customer_success_agent import _all_api_keys
            num_keys = len(_all_api_keys)

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
                    is_rate_limit = any(x in err_str or x in err_str.lower() for x in ["429", "RESOURCE_EXHAUSTED", "too many requests", "rate_limit"])
                    
                    if is_rate_limit:
                        if attempt < MAX_RETRIES:
                            new_key = rotate_client()
                            config = get_run_config()
                            masked_key = f"{new_key[:6]}...{new_key[-4:]}"
                            
                            # If we still have keys to try in this "round", don't wait 60s
                            if attempt < num_keys:
                                delay = 2 # Small gap to avoid burst limit
                                logger.warning(f"[QUOTA] Hit limit. Trying next key {masked_key} in {delay}s...")
                            else:
                                delay = RETRY_BASE_DELAY
                                logger.warning(f"[QUOTA] All keys likely throttled. Waiting {delay}s for reset...")
                            
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise
                    else:
                        # Non-rate limit error (e.g. 404, 500)
                        logger.error(f"[AGENT ERROR] {err_str}")
                        if attempt < MAX_RETRIES:
                            rotate_client()
                            config = get_run_config()
                            await asyncio.sleep(1)
                            continue
                        raise

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
                # Include tracking ID in the message if available
                msg_ticket_id = message.get("ticket_id")
                if msg_ticket_id:
                    tracking_footer = (
                        f"\n\n---\nYour Tracking ID: {msg_ticket_id}\n"
                        f"Track your request at: http://localhost:3000/portal/status"
                    )
                    final_msg_with_tracking = final_msg + tracking_footer
                else:
                    final_msg_with_tracking = final_msg
                await self._fallback_deliver(channel, customer_email, customer_phone, final_msg_with_tracking)

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
        """Finds or creates a customer in the PostgreSQL DB with cross-channel identity matching.

        Identity Resolution Logic (Spec US1):
        - If phone matches an existing record, link to that customer_id even if email differs.
        - Any email discrepancy is logged in customer metadata to preserve history.
        """
        from production.agent.tools import register_customer_identifier, resolve_customer_by_identifier
        conn = await get_db_conn()
        try:
            customer_id = None
            matched_via = None

            # 1. Try cross-channel identity matching (phone first for WhatsApp)
            if phone:
                customer_id = await resolve_customer_by_identifier(conn, "whatsapp", phone)
                if customer_id:
                    matched_via = "phone"
            if not customer_id and email:
                customer_id = await resolve_customer_by_identifier(conn, "email", email)
                if customer_id:
                    matched_via = "email"

            # 2. Fallback to direct DB lookups
            if not customer_id and phone:
                row = await conn.fetchrow("SELECT id FROM customers WHERE phone = $1", phone)
                if row:
                    customer_id = row['id']
                    matched_via = "phone_direct"
            if not customer_id and email:
                row = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", email)
                if row:
                    customer_id = row['id']
                    matched_via = "email_direct"

            # 3. Create new customer if not found
            if not customer_id:
                customer_id = await conn.fetchval(
                    "INSERT INTO customers (email, name, phone) VALUES ($1, $2, $3) RETURNING id",
                    email, name or "Customer", phone
                )
                matched_via = "new"

            # 4. Log email discrepancy if matched via phone but email differs (US1 requirement)
            if matched_via and "phone" in matched_via and email:
                existing = await conn.fetchrow("SELECT email, metadata FROM customers WHERE id = $1", customer_id)
                if existing and existing["email"] and existing["email"] != email:
                    import json as _json
                    metadata = _json.loads(existing["metadata"]) if existing["metadata"] else {}
                    alt_emails = metadata.get("alternate_emails", [])
                    if email not in alt_emails:
                        alt_emails.append(email)
                        metadata["alternate_emails"] = alt_emails
                        await conn.execute(
                            "UPDATE customers SET metadata = $1::jsonb WHERE id = $2",
                            _json.dumps(metadata), customer_id
                        )
                        logger.info(f"[IDENTITY] Logged alternate email {email} for customer {customer_id}")

            # 5. Update phone on customer record if missing
            if phone and customer_id:
                existing_phone = await conn.fetchval("SELECT phone FROM customers WHERE id = $1", customer_id)
                if not existing_phone:
                    await conn.execute("UPDATE customers SET phone = $1 WHERE id = $2", phone, customer_id)

            # 6. Register identifiers for future cross-channel matching
            if email:
                await register_customer_identifier(conn, customer_id, "email", email)
            if phone:
                await register_customer_identifier(conn, customer_id, "whatsapp", phone)

            logger.info(f"[IDENTITY] Resolved customer {customer_id} via {matched_via} (email={email}, phone={phone})")
            return str(customer_id)
        finally:
            await conn.close()

if __name__ == "__main__":
    processor = UnifiedMessageProcessor()
    asyncio.run(processor.start())
