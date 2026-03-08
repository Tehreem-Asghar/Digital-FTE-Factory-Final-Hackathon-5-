# tools.py
import os
import json
import uuid
import asyncpg
import httpx
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from agents import function_tool
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5433/fte_db")
GEMINI_API_KEY = os.getenv("api_key")

def _get_active_key():
    """Get the currently active Gemini API key (supports rotation)."""
    try:
        from production.agent.customer_success_agent import get_current_api_key
        return get_current_api_key()
    except ImportError:
        return GEMINI_API_KEY

def _rotate_global_client():
    """Trigger rotation on global client if we hit a rate limit in a tool."""
    try:
        from production.agent.customer_success_agent import rotate_client
        return rotate_client()
    except ImportError:
        return GEMINI_API_KEY

async def get_db_conn():
    return await asyncpg.connect(DATABASE_URL)

async def analyze_sentiment(text: str) -> float:
    """Analyze sentiment using keyword fallback first to save Gemini quota."""
    # Keyword-based analysis (word boundary matching)
    import re
    negative_words = ["angry", "furious", "terrible", "worst", "hate", "sue", "lawyer",
                      "legal", "scam", "fraud", "stupid", "useless", "damn", "hell",
                      "broken", "waste", "disappointed"]
    text_lower = text.lower()
    neg_count = sum(1 for w in negative_words if re.search(r'\b' + re.escape(w) + r'\b', text_lower))
    
    if neg_count >= 2:
        return 0.2
    
    # Only use API if the message is long and seems complex
    if len(text) > 100:
        for attempt in range(2): 
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={_get_active_key()}"
                    payload = {
                        "contents": [{"parts": [{"text": (
                            f"Sentiment of this: {text}. Return ONLY number 0.0 to 1.0."
                        )}]}],
                        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 5}
                    }
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        text_val = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return max(0.0, min(1.0, float(text_val)))
                    elif response.status_code == 429:
                        _rotate_global_client()
            except:
                break

    return 0.7


async def register_customer_identifier(conn, customer_id: uuid.UUID, id_type: str, id_value: str):
    """Register a customer identifier for cross-channel matching."""
    try:
        await conn.execute(
            "INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified) "
            "VALUES ($1, $2, $3, TRUE) ON CONFLICT (identifier_type, identifier_value) DO NOTHING",
            customer_id, id_type, id_value
        )
    except Exception as e:
        logger.warning(f"Failed to register identifier {id_type}={id_value}: {e}")


async def resolve_customer_by_identifier(conn, id_type: str, id_value: str):
    """Try to find a customer by any identifier (cross-channel matching)."""
    row = await conn.fetchrow(
        "SELECT customer_id FROM customer_identifiers WHERE identifier_type = $1 AND identifier_value = $2",
        id_type, id_value
    )
    return row["customer_id"] if row else None


async def get_or_create_conversation(conn, customer_id: uuid.UUID, channel: str) -> uuid.UUID:
    """Get active conversation or create new one."""
    row = await conn.fetchrow(
        "SELECT id FROM conversations WHERE customer_id = $1 AND status = 'active' "
        "ORDER BY started_at DESC LIMIT 1",
        customer_id
    )
    if row:
        return row["id"]
    conv_id = await conn.fetchval(
        "INSERT INTO conversations (customer_id, initial_channel, status) "
        "VALUES ($1, $2, 'active') RETURNING id",
        customer_id, channel
    )
    return conv_id


async def log_message(conn, conversation_id: uuid.UUID, channel: str, direction: str,
                      role: str, content: str, delivery_status: str = "pending"):
    """Log a message to the messages table."""
    await conn.execute(
        "INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        conversation_id, channel, direction, role, content, delivery_status
    )


async def get_embedding(text: str) -> List[float]:
    """Generates an embedding vector trying multiple models and versions."""
    import httpx
    # Try different combinations of versions and models
    attempts = [
        ("v1beta", "gemini-embedding-001"),
        ("v1beta", "text-embedding-004"),
        ("v1", "text-embedding-004"),
        ("v1beta", "embedding-001"),
        ("v1", "embedding-001"),
    ]
    
    last_error = ""
    for rotate_attempt in range(2): # Try rotating keys if we hit rate limits
        async with httpx.AsyncClient() as client:
            for version, model in attempts:
                url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:embedContent?key={_get_active_key()}"
                payload = {
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": 768,
                }
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        return response.json()["embedding"]["values"][:768]
                    elif response.status_code == 429:
                        last_error = f"Rate limit hit on {model}"
                        break # Exit the model loop to rotate and try again
                    last_error = response.text
                except Exception as e:
                    last_error = str(e)
            
            if "Rate limit" in last_error:
                logger.warning(f"Embeddings hit 429, rotating key (attempt {rotate_attempt+1})")
                _rotate_global_client()
            else:
                break # Not a rate limit, or we're done
                
    raise Exception(f"All embedding attempts failed. Last error: {last_error}")

# --- Tool Input Schemas ---

class KBSearchInput(BaseModel):
    query: str = Field(description="The search query for the knowledge base.")
    max_results: int = Field(default=3, description="Maximum results to return.")

class TicketInput(BaseModel):
    customer_id: str = Field(description="Unique identifier for the customer (Email).")
    issue: str = Field(description="Summary of the customer's issue.")
    priority: str = Field(default="medium", description="Priority level (low, medium, high).")
    channel: str = Field(description="The source channel (email, whatsapp, web_form).")

class HistoryInput(BaseModel):
    customer_id: str = Field(description="Unique identifier for the customer (Email).")

class EscalationInput(BaseModel):
    ticket_id: str = Field(description="The ID of the ticket to escalate.")
    reason: str = Field(description="Reason for escalation.")

class ResponseInput(BaseModel):
    ticket_id: str = Field(description="The ID of the ticket being responded to.")
    message: str = Field(description="The message content to send.")
    channel: str = Field(description="The target channel for the response.")

# --- Production Tools ---

@function_tool
async def search_knowledge_base(input: KBSearchInput) -> str:
    """Search product documentation using semantic or text search."""
    conn = await get_db_conn()
    try:
        results = []
        try:
            # 1. Try Semantic Search
            query_vector = await get_embedding(input.query)
            vector_str = f"[{','.join(map(str, query_vector))}]"
            results = await conn.fetch(
                "SELECT title, content, 1 - (embedding <=> $1) as score FROM knowledge_base ORDER BY embedding <=> $1 LIMIT $2",
                vector_str, input.max_results
            )
        except:
            # 2. Fallback to Flexible Keyword Search if embeddings fail
            # Split query into words and search for any significant word
            words = [f"%{w}%" for w in input.query.split() if len(w) > 4] # Words longer than 4 chars
            
            results = await conn.fetch(
                """
                SELECT title, content, 0.8 as score 
                FROM knowledge_base 
                WHERE content ILIKE ANY($1) OR title ILIKE ANY($1) 
                LIMIT $2
                """,
                words, input.max_results
            )
        
        if not results:
            return "No relevant documentation found in the knowledge base."
        
        formatted = [f"**{r['title']}**\n{r['content']}" for r in results]
        return "\n\n---\n\n".join(formatted)
    finally:
        await conn.close()

@function_tool
async def create_ticket(input: TicketInput) -> str:
    """Create a support ticket in the PostgreSQL database."""
    conn = await get_db_conn()
    try:
        # Detect if customer_id is email or phone
        is_email = "@" in input.customer_id
        id_type = "email" if is_email else "whatsapp"
        
        # 1. Cross-channel identity matching
        cust_id = await resolve_customer_by_identifier(conn, id_type, input.customer_id)

        if not cust_id:
            # 2. Fallback to direct lookup
            if is_email:
                cust_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", input.customer_id)
            else:
                cust_id = await conn.fetchval("SELECT id FROM customers WHERE phone = $1", input.customer_id)

        if not cust_id:
            # 3. Create a new customer record
            if is_email:
                cust_id = await conn.fetchval(
                    "INSERT INTO customers (email, name) VALUES ($1, $2) RETURNING id",
                    input.customer_id, "Unknown"
                )
            else:
                cust_id = await conn.fetchval(
                    "INSERT INTO customers (phone, name) VALUES ($1, $2) RETURNING id",
                    input.customer_id, "Unknown"
                )

        # Register identifier for future cross-channel matching
        await register_customer_identifier(conn, cust_id, id_type, input.customer_id)

        # Create or get active conversation
        conv_id = await get_or_create_conversation(conn, cust_id, input.channel)

        # Create ticket linked to conversation
        ticket_id = await conn.fetchval(
            "INSERT INTO tickets (customer_id, conversation_id, source_channel, status, priority) "
            "VALUES ($1, $2, $3, 'open', $4) RETURNING id",
            cust_id, conv_id, input.channel, input.priority
        )

        # Log the inbound message
        await log_message(conn, conv_id, input.channel, "inbound", "customer", input.issue)

        return f"Ticket created successfully: {ticket_id}. Inform the user that their request is being handled."
    finally:
        await conn.close()

@function_tool
async def get_customer_history(input: HistoryInput) -> str:
    """Retrieve customer's conversation history across all channels (unified cross-channel view)."""
    conn = await get_db_conn()
    try:
        is_email = "@" in input.customer_id
        cust_id = None

        # 1. Try identifier-based lookup first (cross-channel)
        id_type = "email" if is_email else "whatsapp"
        cust_id = await resolve_customer_by_identifier(conn, id_type, input.customer_id)

        # 2. Fallback to direct lookup
        if not cust_id:
            if is_email:
                cust_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", input.customer_id)
            else:
                cust_id = await conn.fetchval("SELECT id FROM customers WHERE phone = $1", input.customer_id)

        if not cust_id:
            return "No previous history found for this customer."

        # 3. Pull unified cross-channel history (includes channel info)
        results = await conn.fetch(
            "SELECT m.role, m.content, m.channel, m.direction, m.created_at, c.initial_channel "
            "FROM messages m "
            "JOIN conversations c ON m.conversation_id = c.id "
            "WHERE c.customer_id = $1 "
            "ORDER BY m.created_at DESC LIMIT 15",
            cust_id
        )

        if not results:
            return "No previous history found for this customer."
        return json.dumps([dict(r) for r in results], default=str)
    finally:
        await conn.close()

@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """Update ticket status to escalated and log reason."""
    conn = await get_db_conn()
    try:
        ticket_uuid = uuid.UUID(input.ticket_id)
        await conn.execute(
            "UPDATE tickets SET status = 'escalated', resolution_notes = $1 WHERE id = $2",
            f"Escalation Reason: {input.reason}", ticket_uuid
        )

        # Update conversation status if linked
        conv_id = await conn.fetchval(
            "SELECT conversation_id FROM tickets WHERE id = $1", ticket_uuid
        )
        if conv_id:
            await conn.execute(
                "UPDATE conversations SET status = 'escalated', escalated_to = 'human_agent', "
                "resolution_type = 'escalated' WHERE id = $1",
                conv_id
            )

        # Log escalation metric
        await conn.execute(
            "INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions) "
            "VALUES ('escalation', 1, "
            "(SELECT source_channel FROM tickets WHERE id = $1), $2)",
            ticket_uuid, json.dumps({"ticket_id": input.ticket_id, "reason": input.reason})
        )

        return f"Ticket {input.ticket_id} escalated to human specialist."
    finally:
        await conn.close()

@function_tool
async def send_response(input: ResponseInput) -> str:
    """Log the outgoing message, apply channel formatting, and trigger delivery."""
    from production.agent.formatters import format_for_channel
    from production.channels.whatsapp_handler import WhatsAppHandler
    from production.channels.gmail_handler import GmailHandler

    print(f"\n[TOOL CALL] send_response called for ticket {input.ticket_id} on channel {input.channel}")
    
    conn = await get_db_conn()
    try:
        # 1. Get ticket and conversation info
        ticket = await conn.fetchrow(
            "SELECT customer_id, conversation_id, source_channel FROM tickets WHERE id = $1",
            uuid.UUID(input.ticket_id)
        )
        if not ticket:
            return f"Warning: Ticket {input.ticket_id} not found, but response noted."

        conv_id = ticket["conversation_id"]
        customer_id = ticket["customer_id"]
        channel = input.channel or ticket["source_channel"]

        # 2. Get customer info (name, phone, email) for delivery
        customer = await conn.fetchrow("SELECT name, email, phone FROM customers WHERE id = $1", customer_id)
        customer_name = customer["name"] if customer else "Customer"
        customer_email = customer["email"] if customer else None
        customer_phone = customer["phone"] if customer else None
        
        print(f"[DEBUG] Customer Info: ID={customer_id}, Name={customer_name}, Phone={customer_phone}")

        # 3. Apply channel-specific formatting
        formatted_message = format_for_channel(input.message, channel, customer_name)

        # 4. Trigger Real Delivery based on Channel
        delivery_status = "sent"
        delivery_error = None

        if channel.lower() == "whatsapp":
            print(f"[DEBUG] Attempting WhatsApp delivery to channel: {channel}")
            wa_handler = WhatsAppHandler()
            # Try to use the phone from customer record
            target_phone = customer_phone
            if not target_phone:
                print("[DEBUG] Phone not in customer record, checking identifiers...")
                # Fallback: find phone in identifiers table
                target_phone = await conn.fetchval(
                    "SELECT identifier_value FROM customer_identifiers WHERE customer_id = $1 AND identifier_type = 'whatsapp'",
                    customer_id
                )
            
            print(f"[DEBUG] Target Phone identified as: {target_phone}")
            
            if target_phone:
                try:
                    print(f"[DEBUG] Calling Meta Cloud API for {target_phone}...")
                    resp = await wa_handler.send_message(target_phone, formatted_message)
                    print(f"[SUCCESS] Meta API Response: {resp}")
                    print(f"[SUCCESS] WhatsApp message delivered to {target_phone}")
                except Exception as e:
                    delivery_status = "failed"
                    delivery_error = str(e)
                    print(f"[ERROR] WhatsApp delivery failed with exception: {e}")
                    logger.error(f"WhatsApp delivery failed: {e}")
            else:
                delivery_status = "failed"
                delivery_error = "No phone number found for WhatsApp delivery"
                print("[ERROR] No target phone found for this customer.")

        elif channel.lower() == "web_form":
            # Web form: response is displayed on-screen via polling, no email needed
            print(f"[WEB_FORM] Response saved to DB for on-screen display (ticket {input.ticket_id})")
            delivery_status = "sent"

        elif channel.lower() == "email":
            if customer_email:
                try:
                    gmail = GmailHandler()
                    # Get ticket subject from the inbound message
                    subject_row = await conn.fetchval(
                        "SELECT content FROM messages WHERE conversation_id = $1 AND direction = 'inbound' "
                        "ORDER BY created_at ASC LIMIT 1",
                        conv_id
                    ) if conv_id else None
                    subject = f"Re: {subject_row[:50]}" if subject_row else "SaaSFlow Support Response"
                    # Append tracking ID to the email body
                    email_body = (
                        f"{formatted_message}\n\n"
                        f"---\n"
                        f"Your Tracking ID: {input.ticket_id}\n"
                        f"Track your request at: http://localhost:3000/portal/status"
                    )
                    resp = await gmail.send_email_smtp(customer_email, subject, email_body)
                    print(f"[SUCCESS] Email sent to {customer_email}: {resp}")
                except Exception as e:
                    delivery_status = "failed"
                    delivery_error = str(e)
                    print(f"[ERROR] Email delivery failed: {e}")
                    logger.error(f"Email delivery failed: {e}")
            else:
                delivery_status = "failed"
                delivery_error = "No email found for delivery"

        # 5. Run sentiment analysis on the original customer message (from inbound)
        last_inbound = await conn.fetchval(
            "SELECT content FROM messages WHERE conversation_id = $1 AND direction = 'inbound' "
            "ORDER BY created_at DESC LIMIT 1",
            conv_id
        ) if conv_id else None

        if last_inbound:
            sentiment = await analyze_sentiment(last_inbound)
            # Update conversation sentiment
            if conv_id:
                await conn.execute(
                    "UPDATE conversations SET sentiment_score = $1 WHERE id = $2",
                    sentiment, conv_id
                )

        # 6. Log outbound message to DB
        if conv_id:
            await log_message(conn, conv_id, channel, "outbound", "agent", formatted_message, delivery_status)

        # 7. Record metric
        await conn.execute(
            "INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions) "
            "VALUES ('message_processed', 0, $1, $2)",
            channel, json.dumps({
                "ticket_id": input.ticket_id, 
                "type": "response_sent", 
                "delivery": delivery_status,
                "error": delivery_error
            })
        )

        if delivery_status == "failed":
            return f"Response noted, but delivery to {channel} failed: {delivery_error}"
        
        return f"Response delivered to {channel} for ticket {input.ticket_id}."
    except Exception as e:
        logger.error(f"send_response error: {e}")
        return f"Response noted for ticket {input.ticket_id} (delivery pending)."
    finally:
        await conn.close()
