# web_form_handler.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
import logging
from production.agent.tools import get_db_conn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/support", tags=["support-form"])

class SupportFormSubmission(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: Optional[str] = "general"
    message: str
    priority: Optional[str] = "medium"

@router.post("/submit")
async def submit_support_form(submission: SupportFormSubmission, request: Request):
    """Submits a support form, pre-creates ticket in DB, and publishes to Kafka."""
    # Pre-create ticket in database so the tracking ID is real and queryable
    conn = await get_db_conn()
    try:
        # Find or create customer
        cust_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", submission.email)
        if not cust_id:
            cust_id = await conn.fetchval(
                "INSERT INTO customers (email, name) VALUES ($1, $2) RETURNING id",
                submission.email, submission.name
            )

        # Create conversation
        conv_id = await conn.fetchval(
            "INSERT INTO conversations (customer_id, initial_channel, status) VALUES ($1, 'web_form', 'active') RETURNING id",
            cust_id
        )

        # Create ticket in DB — this is the REAL ticket_id
        ticket_id = str(await conn.fetchval(
            "INSERT INTO tickets (customer_id, conversation_id, source_channel, status, priority) "
            "VALUES ($1, $2, 'web_form', 'open', $3) RETURNING id",
            cust_id, conv_id, submission.priority or "medium"
        ))

        # Log the inbound message
        await conn.execute(
            "INSERT INTO messages (conversation_id, channel, direction, role, content) "
            "VALUES ($1, 'web_form', 'inbound', 'customer', $2)",
            conv_id, submission.message
        )
    finally:
        await conn.close()

    message_data = {
        "channel": "web_form",
        "ticket_id": ticket_id,
        "name": submission.name,
        "email": submission.email,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority
    }
    
    # Get the producer from app state to avoid multiple instances hanging
    producer = getattr(request.app.state, "kafka_producer", None)

    if producer:
        try:
            await producer.publish("fte.tickets.incoming", message_data)
            return {
                "ticket_id": ticket_id,
                "message": "Thank you! Our AI assistant will respond shortly."
            }
        except Exception as e:
            logger.warning(f"Kafka unavailable, saving to pending_ingestion: {e}")

    # Fail-safe: save to DB when Kafka is down or producer not available
    from production.database.queries import save_pending_message
    await save_pending_message("fte.tickets.incoming", message_data)
    return {
        "ticket_id": ticket_id,
        "message": "Thank you! Your request has been received and will be processed shortly."
    }

@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Retrieves the status, details, and messages for a specific ticket."""
    conn = await get_db_conn()
    try:
        try:
            u_id = uuid.UUID(ticket_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ticket ID format")

        ticket = await conn.fetchrow(
            "SELECT t.id, t.status, t.priority, t.source_channel, t.created_at, "
            "t.conversation_id, c.name as customer_name, c.email as customer_email "
            "FROM tickets t LEFT JOIN customers c ON t.customer_id = c.id "
            "WHERE t.id = $1", u_id
        )
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        result = dict(ticket)
        result["ticket_id"] = str(result.pop("id"))
        result["last_updated"] = result["created_at"]

        # Fetch conversation messages if available
        messages = []
        if ticket["conversation_id"]:
            rows = await conn.fetch(
                "SELECT role, content, channel, direction, created_at, delivery_status "
                "FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC",
                ticket["conversation_id"]
            )
            messages = [dict(r) for r in rows]

        result["messages"] = messages
        return result
    finally:
        await conn.close()
