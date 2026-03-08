# main.py
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime
from production.utils.kafka_client import FTEKafkaProducer
from production.channels.web_form_handler import router as web_form_router
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.gmail_handler import GmailHandler
from production.agent.tools import get_db_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# --- Initialize Global Handlers ---
whatsapp_handler = WhatsAppHandler()
gmail_handler = GmailHandler()

# --- Pydantic models for Swagger UI visibility ---

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

class EmailSubmission(BaseModel):
    """Simple email support request."""
    name: str = "Customer"
    email: str = "user@gmail.com"
    subject: str = "Help needed"
    message: str = "I need help with my account"

class WhatsAppSubmission(BaseModel):
    phone: str
    message: str

# --- App Lifecycle ---

@app.on_event("startup")
async def startup():
    # Initialize shared Kafka producer in app state
    producer = FTEKafkaProducer()
    try:
        await producer.start()
        app.state.kafka_producer = producer
        logger.info("Kafka Producer started and attached to app state.")
    except Exception as e:
        logger.warning(f"Kafka unavailable at startup, will use fail-safe ingestion: {e}")
        app.state.kafka_producer = None

@app.on_event("shutdown")
async def shutdown():
    producer = getattr(app.state, "kafka_producer", None)
    if producer:
        await producer.stop()
        logger.info("Kafka Producer stopped.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "digital-fte-api"}

# --- Webhook handlers for Gmail and WhatsApp ---

@app.post("/webhooks/gmail")
async def gmail_webhook(payload: GmailWebhookPayload):
    """Handle Gmail Pub/Sub notifications."""
    data = payload.dict()
    result = await gmail_handler.process_pubsub_notification(data)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail"))
    return result

@app.post("/support/email")
async def submit_email_support(submission: EmailSubmission):
    """Submit email support request directly."""
    # Pre-create ticket in DB so the tracking ID is real
    conn = await get_db_conn()
    try:
        cust_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", submission.email)
        if not cust_id:
            cust_id = await conn.fetchval(
                "INSERT INTO customers (email, name) VALUES ($1, $2) RETURNING id",
                submission.email, submission.name
            )
        conv_id = await conn.fetchval(
            "INSERT INTO conversations (customer_id, initial_channel, status) VALUES ($1, 'email', 'active') RETURNING id",
            cust_id
        )
        ticket_id = str(await conn.fetchval(
            "INSERT INTO tickets (customer_id, conversation_id, source_channel, status, priority) "
            "VALUES ($1, $2, 'email', 'open', 'medium') RETURNING id",
            cust_id, conv_id
        ))
        await conn.execute(
            "INSERT INTO messages (conversation_id, channel, direction, role, content) "
            "VALUES ($1, 'email', 'inbound', 'customer', $2)",
            conv_id, f"[Subject: {submission.subject}] {submission.message}"
        )
    finally:
        await conn.close()

    message_data = {
        "channel": "email",
        "ticket_id": ticket_id,
        "email": submission.email,
        "name": submission.name,
        "content": f"[Subject: {submission.subject}] {submission.message}",
        "metadata": {
            "subject": submission.subject,
            "source": "email_form",
        }
    }
    producer = getattr(app.state, "kafka_producer", None)
    if producer:
        try:
            await producer.publish("fte.tickets.incoming", message_data)
        except Exception as e:
            logger.warning(f"Kafka unavailable for email, saving to pending_ingestion: {e}")
            from production.database.queries import save_pending_message
            await save_pending_message("fte.tickets.incoming", message_data)
    else:
        from production.database.queries import save_pending_message
        await save_pending_message("fte.tickets.incoming", message_data)
    return {
        "status": "received",
        "ticket_id": ticket_id,
        "message": "Email support request queued for AI processing.",
    }

@app.post("/support/whatsapp")
async def submit_whatsapp_support(submission: WhatsAppSubmission):
    """Testing endpoint for WhatsApp via UI."""
    # Pre-create ticket in DB so the tracking ID is real
    conn = await get_db_conn()
    try:
        cust_id = await conn.fetchval("SELECT id FROM customers WHERE phone = $1", submission.phone)
        if not cust_id:
            cust_id = await conn.fetchval(
                "INSERT INTO customers (phone, name) VALUES ($1, $2) RETURNING id",
                submission.phone, "WhatsApp User"
            )
        conv_id = await conn.fetchval(
            "INSERT INTO conversations (customer_id, initial_channel, status) VALUES ($1, 'whatsapp', 'active') RETURNING id",
            cust_id
        )
        ticket_id = str(await conn.fetchval(
            "INSERT INTO tickets (customer_id, conversation_id, source_channel, status, priority) "
            "VALUES ($1, $2, 'whatsapp', 'open', 'medium') RETURNING id",
            cust_id, conv_id
        ))
        await conn.execute(
            "INSERT INTO messages (conversation_id, channel, direction, role, content) "
            "VALUES ($1, 'whatsapp', 'inbound', 'customer', $2)",
            conv_id, submission.message
        )
    finally:
        await conn.close()

    message_data = {
        "channel": "whatsapp",
        "ticket_id": ticket_id,
        "phone": submission.phone,
        "content": submission.message,
        "metadata": {
            "source": "whatsapp_form",
        }
    }
    producer = getattr(app.state, "kafka_producer", None)
    if producer:
        try:
            await producer.publish("fte.tickets.incoming", message_data)
        except Exception as e:
            logger.warning(f"Kafka unavailable for whatsapp, saving to pending_ingestion: {e}")
            from production.database.queries import save_pending_message
            await save_pending_message("fte.tickets.incoming", message_data)
    else:
        from production.database.queries import save_pending_message
        await save_pending_message("fte.tickets.incoming", message_data)
    return {
        "status": "received",
        "ticket_id": ticket_id,
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

# --- Dashboard API Endpoints ---

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

        status_counts = await conn.fetch("SELECT status, COUNT(*) as count FROM tickets GROUP BY status")
        channel_counts = await conn.fetch("SELECT source_channel as channel, COUNT(*) as count FROM tickets GROUP BY source_channel")
        priority_counts = await conn.fetch("SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority")

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

# --- Simplified endpoints (rest unchanged but using shared producer) ---
@app.get("/api/tickets")
async def get_all_tickets():
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("SELECT t.id, t.status, t.priority, t.source_channel, t.created_at, c.name as customer_name, c.email as customer_email, t.category, t.resolution_notes, t.resolved_at, conv.id as conversation_id FROM tickets t LEFT JOIN customers c ON t.customer_id = c.id LEFT JOIN conversations conv ON t.conversation_id = conv.id ORDER BY t.created_at DESC")
        return [dict(r) for r in rows]
    finally: await conn.close()

@app.get("/api/tickets/{ticket_id}")
async def get_ticket_details(ticket_id: str):
    conn = await get_db_conn()
    try:
        ticket = await conn.fetchrow("""
            SELECT t.*, c.name as customer_name, c.email as customer_email, c.phone as customer_phone,
                   conv.id as conversation_id, conv.initial_channel
            FROM tickets t
            LEFT JOIN customers c ON t.customer_id = c.id
            LEFT JOIN conversations conv ON t.conversation_id = conv.id
            WHERE t.id = $1
        """, ticket_id)
        
        if not ticket:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get conversation messages
        messages = await conn.fetch("""
            SELECT id, channel, direction, role, content, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """, ticket['conversation_id'])
        
        return {
            'ticket': dict(ticket),
            'messages': [dict(m) for m in messages]
        }
    finally:
        await conn.close()

@app.get("/api/customers")
async def get_all_customers():
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT c.id, c.name, c.email, c.phone, c.created_at, COUNT(t.id) as ticket_count
            FROM customers c
            LEFT JOIN tickets t ON c.id = t.customer_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@app.get("/api/customers/{customer_id}")
async def get_customer_details(customer_id: str):
    conn = await get_db_conn()
    try:
        customer = await conn.fetchrow("""
            SELECT c.*, COUNT(t.id) as ticket_count
            FROM customers c
            LEFT JOIN tickets t ON c.id = t.customer_id
            WHERE c.id = $1
            GROUP BY c.id
        """, customer_id)
        
        if not customer:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get customer's tickets
        tickets = await conn.fetch("""
            SELECT t.id, t.status, t.priority, t.source_channel, t.created_at, t.category
            FROM tickets t
            WHERE t.customer_id = $1
            ORDER BY t.created_at DESC
            LIMIT 20
        """, customer_id)
        
        # Get customer's conversations
        conversations = await conn.fetch("""
            SELECT conv.id, conv.initial_channel, conv.status, conv.started_at
            FROM conversations conv
            WHERE conv.customer_id = $1
            ORDER BY conv.started_at DESC
            LIMIT 10
        """, customer_id)
        
        return {
            'customer': dict(customer),
            'tickets': [dict(t) for t in tickets],
            'conversations': [dict(c) for c in conversations]
        }
    finally:
        await conn.close()

@app.get("/api/conversations")
async def get_all_conversations():
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT conv.id, conv.initial_channel, conv.status, 
                   c.name as customer_name, c.email as customer_email, conv.started_at
            FROM conversations conv
            LEFT JOIN customers c ON conv.customer_id = c.id
            ORDER BY conv.started_at DESC
            LIMIT 50
        """)
        result = []
        for r in rows:
            d = dict(r)
            # Get sentiment_score separately to avoid type issues
            sentiment = await conn.fetchval("SELECT sentiment_score FROM conversations WHERE id = $1", d['id'])
            d['sentiment_score'] = float(sentiment) if sentiment is not None else 0.0
            result.append(d)
        return result
    finally:
        await conn.close()

@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    conn = await get_db_conn()
    try:
        rows = await conn.fetch("""
            SELECT id, channel, direction, role, content, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """, conversation_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

# --- Mock Meta WhatsApp Cloud API (for E2E testing) ---

@app.post("/mock/meta/send")
async def mock_meta_send(request: Request):
    """Mock Meta WhatsApp Cloud API endpoint for E2E testing.
    Mirrors the response structure of POST /v17.0/{phone_number_id}/messages."""
    import uuid as _uuid
    body = await request.json()
    to_phone = body.get("to", "unknown")
    msg_type = body.get("type", "text")
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": to_phone, "wa_id": to_phone}],
        "messages": [{"id": f"wamid.mock_{_uuid.uuid4().hex[:12]}"}]
    }


@app.get("/mock/meta/health")
async def mock_meta_health():
    """Health check for the mock Meta server."""
    return {"status": "ok", "mock": True}


@app.get("/metrics/channels")
async def get_metrics_by_channel():
    """Return metrics broken down by channel."""
    conn = await get_db_conn()
    try:
        channels = ["email", "whatsapp", "web_form"]
        result = {}
        for ch in channels:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE initial_channel = $1", ch
            )
            escalated = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE initial_channel = $1 AND status = 'escalated'", ch
            )
            avg_sentiment = await conn.fetchval(
                "SELECT AVG(sentiment_score) FROM conversations WHERE initial_channel = $1 AND sentiment_score IS NOT NULL", ch
            )
            result[ch] = {
                "total_conversations": total or 0,
                "escalated": escalated or 0,
                "avg_sentiment": float(avg_sentiment or 0),
            }
        return result
    finally:
        await conn.close()


@app.get("/customers/lookup")
async def lookup_customer(email: str = None, phone: str = None):
    """Lookup customer by email or phone for cross-channel E2E tests."""
    conn = await get_db_conn()
    try:
        customer = None
        if email:
            customer = await conn.fetchrow("SELECT * FROM customers WHERE email = $1", email)
        elif phone:
            customer = await conn.fetchrow("SELECT * FROM customers WHERE phone = $1", phone)

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        conversations = await conn.fetch(
            "SELECT id, initial_channel, status, started_at FROM conversations "
            "WHERE customer_id = $1 ORDER BY started_at DESC LIMIT 10",
            customer["id"]
        )
        return {
            **dict(customer),
            "conversations": [dict(c) for c in conversations]
        }
    finally:
        await conn.close()


@app.get("/metrics/summary")
async def get_metrics_summary():
    conn = await get_db_conn()
    try:
        total = await conn.fetchrow("SELECT COUNT(*) as total_events, ROUND(AVG(metric_value)::numeric, 2) as avg_latency_ms FROM agent_metrics WHERE metric_name = 'message_processed'")
        return {"status": "ok", "total_messages_processed": total["total_events"], "avg_latency_ms": float(total["avg_latency_ms"] or 0)}
    finally: await conn.close()


# --- Daily Sentiment Reports ---

@app.get("/api/reports/sentiment/daily")
async def get_daily_sentiment_report(days: int = Query(default=7, ge=1, le=90)):
    """Generate daily sentiment report with per-channel breakdown and trends."""
    conn = await get_db_conn()
    try:
        # Daily averages across all channels
        daily_overall = await conn.fetch("""
            SELECT DATE(started_at) as date,
                   ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
                   COUNT(*) as conversation_count,
                   SUM(CASE WHEN sentiment_score < 0.3 THEN 1 ELSE 0 END) as angry_count,
                   SUM(CASE WHEN sentiment_score >= 0.3 AND sentiment_score < 0.6 THEN 1 ELSE 0 END) as concerned_count,
                   SUM(CASE WHEN sentiment_score >= 0.6 THEN 1 ELSE 0 END) as satisfied_count
            FROM conversations
            WHERE sentiment_score IS NOT NULL
              AND started_at >= NOW() - INTERVAL '1 day' * $1
            GROUP BY DATE(started_at)
            ORDER BY DATE(started_at) DESC
        """, days)

        # Per-channel daily breakdown
        channel_breakdown = await conn.fetch("""
            SELECT DATE(started_at) as date,
                   initial_channel as channel,
                   ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
                   COUNT(*) as count
            FROM conversations
            WHERE sentiment_score IS NOT NULL
              AND started_at >= NOW() - INTERVAL '1 day' * $1
            GROUP BY DATE(started_at), initial_channel
            ORDER BY DATE(started_at) DESC, initial_channel
        """, days)

        # Overall summary stats
        summary = await conn.fetchrow("""
            SELECT ROUND(AVG(sentiment_score)::numeric, 3) as overall_avg,
                   ROUND(MIN(sentiment_score)::numeric, 3) as worst_day_score,
                   ROUND(MAX(sentiment_score)::numeric, 3) as best_day_score,
                   COUNT(*) as total_conversations,
                   SUM(CASE WHEN sentiment_score < 0.3 THEN 1 ELSE 0 END) as total_angry,
                   ROUND((SUM(CASE WHEN status = 'escalated' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100), 1) as escalation_rate_pct
            FROM conversations
            WHERE sentiment_score IS NOT NULL
              AND started_at >= NOW() - INTERVAL '1 day' * $1
        """, days)

        return {
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": dict(summary) if summary else {},
            "daily_trends": [dict(r) for r in daily_overall],
            "channel_breakdown": [dict(r) for r in channel_breakdown],
        }
    finally:
        await conn.close()


@app.get("/api/reports/sentiment/today")
async def get_today_sentiment():
    """Quick snapshot of today's sentiment across channels."""
    conn = await get_db_conn()
    try:
        today = await conn.fetch("""
            SELECT initial_channel as channel,
                   ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
                   COUNT(*) as conversations,
                   SUM(CASE WHEN sentiment_score < 0.3 THEN 1 ELSE 0 END) as angry,
                   SUM(CASE WHEN status = 'escalated' THEN 1 ELSE 0 END) as escalated
            FROM conversations
            WHERE sentiment_score IS NOT NULL
              AND DATE(started_at) = CURRENT_DATE
            GROUP BY initial_channel
        """)

        overall = await conn.fetchrow("""
            SELECT ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
                   COUNT(*) as total_conversations
            FROM conversations
            WHERE sentiment_score IS NOT NULL AND DATE(started_at) = CURRENT_DATE
        """)

        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "overall": dict(overall) if overall else {"avg_sentiment": 0, "total_conversations": 0},
            "by_channel": [dict(r) for r in today],
        }
    finally:
        await conn.close()


# --- Learn from Resolved Tickets ---

@app.post("/api/learnings/process")
async def trigger_learning_process():
    """Manually trigger extraction of learnings from resolved tickets."""
    from production.workers.learning_worker import process_resolved_tickets
    try:
        count = await process_resolved_tickets()
        return {"status": "ok", "new_learnings_extracted": count}
    except Exception as e:
        logger.error(f"Learning process failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learnings")
async def get_learnings(category: str = None, limit: int = Query(default=20, ge=1, le=100)):
    """Retrieve extracted resolution learnings, optionally filtered by category."""
    conn = await get_db_conn()
    try:
        if category:
            rows = await conn.fetch("""
                SELECT rl.id, rl.issue_category, rl.issue_summary, rl.resolution_summary,
                       rl.source_channel, rl.resolution_time_hours, rl.was_escalated,
                       rl.keywords, rl.created_at, t.status as ticket_status
                FROM resolution_learnings rl
                LEFT JOIN tickets t ON rl.ticket_id = t.id
                WHERE rl.issue_category = $1
                ORDER BY rl.created_at DESC LIMIT $2
            """, category, limit)
        else:
            rows = await conn.fetch("""
                SELECT rl.id, rl.issue_category, rl.issue_summary, rl.resolution_summary,
                       rl.source_channel, rl.resolution_time_hours, rl.was_escalated,
                       rl.keywords, rl.created_at, t.status as ticket_status
                FROM resolution_learnings rl
                LEFT JOIN tickets t ON rl.ticket_id = t.id
                ORDER BY rl.created_at DESC LIMIT $1
            """, limit)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


@app.get("/api/learnings/search")
async def search_similar_resolutions(query: str = Query(..., min_length=3), limit: int = Query(default=3, ge=1, le=10)):
    """Search past resolution learnings by semantic similarity to find how similar issues were resolved."""
    from production.workers.learning_worker import get_similar_resolutions
    results = await get_similar_resolutions(query, limit)
    return {"query": query, "similar_resolutions": results}
