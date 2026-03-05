# main.py
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from production.utils.kafka_client import FTEKafkaProducer
from production.channels.web_form_handler import router as web_form_router
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.gmail_handler import GmailHandler
from production.agent.tools import get_db_conn

app = FastAPI(title="SaaSFlow Digital FTE API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(web_form_router)

kafka_producer = FTEKafkaProducer()
whatsapp_handler = WhatsAppHandler()
gmail_handler = GmailHandler()

# --- Pydantic models for Swagger UI visibility ---

class WhatsAppContact(BaseModel):
    profile: Dict[str, str] = {"name": "Customer"}

class WhatsAppMessage(BaseModel):
    """Single WhatsApp message from Meta."""
    from_: str = "923001234567"
    text: Dict[str, str] = {"body": "How do I create a board?"}

    class Config:
        populate_by_name = True

class WhatsAppValue(BaseModel):
    messages: List[Dict[str, Any]] = [{"from": "923001234567", "text": {"body": "How do I create a board?"}}]
    contacts: List[Dict[str, Any]] = [{"profile": {"name": "Ali"}}]

class WhatsAppChange(BaseModel):
    value: WhatsAppValue = WhatsAppValue()

class WhatsAppEntry(BaseModel):
    changes: List[WhatsAppChange] = [WhatsAppChange()]

class WhatsAppWebhookPayload(BaseModel):
    """Meta WhatsApp Cloud API webhook payload."""
    entry: List[WhatsAppEntry] = [WhatsAppEntry()]

class GmailPubSubMessage(BaseModel):
    data: str = "eyJlbWFpbEFkZHJlc3MiOiJ1c2VyQGdtYWlsLmNvbSIsImhpc3RvcnlJZCI6IjEyMzQ1In0="
    messageId: str = "msg-test-1"
    publishTime: str = "2026-03-05T10:00:00Z"

class GmailWebhookPayload(BaseModel):
    """Google Cloud Pub/Sub push notification for Gmail."""
    message: GmailPubSubMessage = GmailPubSubMessage()
    subscription: str = "projects/saasflow/subscriptions/gmail"

class SupportSubmission(BaseModel):
    name: str
    email: str
    subject: str
    message: str
    channel: str = "web_form"

class EmailSubmission(BaseModel):
    """Simple email support request — no base64 needed."""
    name: str = "Customer"
    email: str = "user@gmail.com"
    subject: str = "Help needed"
    message: str = "I need help with my account"

# --- Models for WhatsApp and Gmail unchanged ---

@app.on_event("startup")
async def startup():
    await kafka_producer.start()

@app.on_event("shutdown")
async def shutdown():
    await kafka_producer.stop()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "digital-fte-api"}

@app.post("/support/submit")
async def submit_support(submission: SupportSubmission):
    """Handle submissions from the Web Support Form."""
    try:
        await kafka_producer.publish("fte.tickets.incoming", submission.dict())
        return {"status": "received", "message": "Ticket queued for processing."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Webhook handlers for Gmail and WhatsApp unchanged ---

@app.post("/webhooks/gmail")
async def gmail_webhook(payload: GmailWebhookPayload):
    """Handle Gmail Pub/Sub notifications via GmailHandler (raw Pub/Sub format)."""
    data = payload.dict()
    result = await gmail_handler.process_pubsub_notification(data)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result

@app.post("/support/email")
async def submit_email_support(submission: EmailSubmission):
    """Simple email support — user sirf email, name, subject, message bheje. Backend sab handle karega."""

    # Publish to Kafka directly as email channel message
    message_data = {
        "channel": "email",
        "email": submission.email,
        "name": submission.name,
        "content": f"[Subject: {submission.subject}] {submission.message}",
        "metadata": {
            "subject": submission.subject,
            "source": "email_form",
        }
    }
    await kafka_producer.publish("fte.tickets.incoming", message_data)

    return {
        "status": "received",
        "ticket_id": str(uuid.uuid4()),
        "message": f"Email support request queued for AI processing.",
    }

class WhatsAppSubmission(BaseModel):
    phone: str
    message: str

@app.post("/support/whatsapp")
async def submit_whatsapp_support(submission: WhatsAppSubmission):
    """Testing endpoint for WhatsApp via UI."""
    message_data = {
        "channel": "whatsapp",
        "phone": submission.phone,
        "content": submission.message,
        "metadata": {
            "source": "whatsapp_form",
        }
    }
    await kafka_producer.publish("fte.tickets.incoming", message_data)

    return {
        "status": "received",
        "ticket_id": str(uuid.uuid4()),
        "message": "WhatsApp message queued for AI processing.",
    }

@app.get("/webhooks/whatsapp")
async def verify_whatsapp(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Verify Meta Webhook."""
    challenge = await whatsapp_handler.validate_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is not None:
        from fastapi.responses import Response
        return Response(content=str(challenge))
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    """Handle incoming WhatsApp messages from Meta."""
    data = payload.dict()
    await whatsapp_handler.process_webhook(data)
    return {"status": "ok"}

# --- New Dashboard API Endpoints ---

@app.get("/api/tickets")
async def get_all_tickets():
    """List all tickets with customer info, status, channel, priority."""
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT 
                t.id, 
                t.status, 
                t.priority, 
                t.source_channel, 
                t.created_at, 
                c.name as customer_name, 
                c.email as customer_email
            FROM tickets t
            LEFT JOIN customers c ON t.customer_id = c.id
            ORDER BY t.created_at DESC
        """)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@app.get("/api/customers")
async def get_all_customers():
    """List all customers with ticket count."""
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT 
                c.id, 
                c.name, 
                c.email, 
                c.phone, 
                c.created_at,
                COUNT(t.id) as ticket_count
            FROM customers c
            LEFT JOIN tickets t ON c.id = t.customer_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@app.get("/api/conversations")
async def get_all_conversations():
    """List conversations with sentiment, status, customer info."""
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT 
                cv.id, 
                cv.status, 
                cv.sentiment_score, 
                cv.initial_channel, 
                cv.started_at,
                c.name as customer_name,
                c.email as customer_email
            FROM conversations cv
            LEFT JOIN customers c ON cv.customer_id = c.id
            ORDER BY cv.started_at DESC
        """)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get messages for a specific conversation."""
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT role, content, direction, channel, created_at, delivery_status
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """, uuid.UUID(conversation_id))
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Combined dashboard stats for overview."""
    conn = await get_db_conn()
    try:
        total_tickets = await conn.fetchval("SELECT COUNT(*) FROM tickets")
        open_tickets = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
        escalated_tickets = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE status = 'escalated'")
        total_customers = await conn.fetchval("SELECT COUNT(*) FROM customers")
        avg_sentiment = await conn.fetchval("SELECT AVG(sentiment_score) FROM conversations WHERE sentiment_score IS NOT NULL")
        
        # Tickets by status
        status_counts = await conn.fetch("SELECT status, COUNT(*) as count FROM tickets GROUP BY status")
        
        # Tickets by channel
        channel_counts = await conn.fetch("SELECT source_channel as channel, COUNT(*) as count FROM tickets GROUP BY source_channel")
        
        # Tickets by priority
        priority_counts = await conn.fetch("SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority")
        
        # Recent activity (last 10 tickets)
        recent_tickets = await conn.fetch("""
            SELECT t.id, t.status, t.priority, c.name as customer_name, t.created_at
            FROM tickets t
            LEFT JOIN customers c ON t.customer_id = c.id
            ORDER BY t.created_at DESC
            LIMIT 10
        """)

        return {
            "kpis": {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "escalated_tickets": escalated_tickets,
                "total_customers": total_customers,
                "avg_sentiment": float(avg_sentiment or 0),
            },
            "charts": {
                "by_status": [dict(r) for r in status_counts],
                "by_channel": [dict(r) for r in channel_counts],
                "by_priority": [dict(r) for r in priority_counts],
            },
            "recent_tickets": [dict(r) for r in recent_tickets]
        }
    finally:
        await conn.close()

# --- Metrics Endpoints ---

@app.get("/metrics/channels")
async def get_channel_metrics():
    """Returns aggregated metrics per channel from agent_metrics table."""
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT
                channel,
                COUNT(*) as total_events,
                ROUND(AVG(metric_value)::numeric, 2) as avg_latency_ms,
                ROUND(MIN(metric_value)::numeric, 2) as min_latency_ms,
                ROUND(MAX(metric_value)::numeric, 2) as max_latency_ms,
                COUNT(*) FILTER (WHERE metric_name = 'message_processed') as messages_processed,
                COUNT(*) FILTER (WHERE metric_name = 'escalation') as escalations
            FROM agent_metrics
            WHERE channel IS NOT NULL
            GROUP BY channel
            ORDER BY channel
        """)
        channels = {}
        for row in rows:
            channels[row["channel"]] = {
                "total_events": row["total_events"],
                "avg_latency_ms": float(row["avg_latency_ms"] or 0),
                "min_latency_ms": float(row["min_latency_ms"] or 0),
                "max_latency_ms": float(row["max_latency_ms"] or 0),
                "messages_processed": row["messages_processed"],
                "escalations": row["escalations"],
            }
        return {"status": "ok", "channels": channels}
    finally:
        await conn.close()

@app.get("/metrics/summary")
async def get_metrics_summary():
    """Returns overall system metrics summary."""
    conn = await get_db_conn()
    try:
        total = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_events,
                ROUND(AVG(metric_value)::numeric, 2) as avg_latency_ms,
                ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value)::numeric, 2) as p95_latency_ms
            FROM agent_metrics
            WHERE metric_name = 'message_processed'
        """)
        ticket_count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
        escalated_count = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE status = 'escalated'")
        customer_count = await conn.fetchval("SELECT COUNT(*) FROM customers")

        escalation_rate = (escalated_count / ticket_count * 100) if ticket_count > 0 else 0

        return {
            "status": "ok",
            "total_messages_processed": total["total_events"],
            "avg_latency_ms": float(total["avg_latency_ms"] or 0),
            "p95_latency_ms": float(total["p95_latency_ms"] or 0),
            "total_tickets": ticket_count,
            "escalation_rate_pct": round(escalation_rate, 2),
            "total_customers": customer_count,
        }
    finally:
        await conn.close()
