# web_form_handler.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
from production.utils.kafka_client import FTEKafkaProducer
from production.agent.tools import get_db_conn

router = APIRouter(prefix="/support", tags=["support-form"])
kafka_producer = FTEKafkaProducer()

class SupportFormSubmission(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: Optional[str] = "general"
    message: str
    priority: Optional[str] = "medium"

@router.post("/submit")
async def submit_support_form(submission: SupportFormSubmission):
    """Submits a support form and publishes to Kafka."""
    ticket_id = str(uuid.uuid4())
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
    
    await kafka_producer.publish("fte.tickets.incoming", message_data)
    
    return {
        "ticket_id": ticket_id,
        "message": "Thank you! Our AI assistant will respond shortly."
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
