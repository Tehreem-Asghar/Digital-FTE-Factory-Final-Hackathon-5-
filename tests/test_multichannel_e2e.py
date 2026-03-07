# test_multichannel_e2e.py
"""
Automated Multi-Channel E2E Test Suite for SaaSFlow Digital FTE.

Covers:
- Web Form submission + status retrieval
- Gmail Pub/Sub webhook processing
- WhatsApp webhook processing (via Mock Meta)
- Cross-channel customer continuity
- Channel-specific metrics
- Fail-safe ingestion (Kafka down scenario)

Usage:
    pytest tests/test_multichannel_e2e.py -v
    pytest tests/test_multichannel_e2e.py -v -k "TestWebForm"
"""
import pytest
import json
import base64
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

# Use ASGI transport for in-process testing (no real server needed)
BASE_URL = "http://testserver"


@pytest.fixture
async def client():
    """Create async test client with mocked Kafka to avoid real connection."""
    from production.api.main import app

    # Mock the Kafka producer so tests don't need a real broker
    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.publish = AsyncMock()
    mock_producer.health_check = AsyncMock(return_value=True)
    app.state.kafka_producer = mock_producer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


@pytest.fixture
async def client_kafka_down():
    """Create test client with Kafka publish that raises (simulates Kafka down)."""
    from production.api.main import app

    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.publish = AsyncMock(side_effect=Exception("Kafka unreachable"))
    mock_producer.health_check = AsyncMock(return_value=False)
    app.state.kafka_producer = mock_producer

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


# ============================================================
# Test Group 1: Web Form Channel (Required Build)
# ============================================================

class TestWebFormChannel:
    """Test the web support form (required build)."""

    @pytest.mark.asyncio
    async def test_form_submission(self, client):
        """Web form submission should create ticket and return ID."""
        with patch("production.channels.web_form_handler.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=["cust-uuid-1", "conv-uuid-1", "ticket-uuid-1"])
            mock_conn.execute = AsyncMock()
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.post("/support/submit", json={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Help with API",
                "category": "technical",
                "message": "I need help with the API authentication"
            })

            assert response.status_code == 200
            data = response.json()
            assert "ticket_id" in data
            assert data["message"] is not None

    @pytest.mark.asyncio
    async def test_form_validation_missing_fields(self, client):
        """Form should validate required fields."""
        response = await client.post("/support/submit", json={"name": "Test"})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_ticket_status_retrieval(self, client):
        """Should be able to check ticket status after submission."""
        import uuid
        ticket_uuid = uuid.uuid4()

        with patch("production.channels.web_form_handler.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value={
                "id": ticket_uuid,
                "status": "open",
                "priority": "medium",
                "source_channel": "web_form",
                "created_at": "2026-03-08T10:00:00",
                "conversation_id": uuid.uuid4(),
                "customer_name": "Test User",
                "customer_email": "test@example.com",
            })
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.get(f"/support/ticket/{ticket_uuid}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["open", "processing", "resolved", "escalated"]


# ============================================================
# Test Group 2: Email Channel (Gmail)
# ============================================================

class TestEmailChannel:
    """Test Gmail integration."""

    @pytest.mark.asyncio
    async def test_gmail_webhook_processing(self, client):
        """Gmail webhook should process incoming emails."""
        from production.api.main import gmail_handler

        encoded = base64.b64encode(json.dumps({
            "emailAddress": "user@gmail.com",
            "historyId": "12345"
        }).encode()).decode()

        with patch.object(gmail_handler, "process_pubsub_notification", new=AsyncMock(
            return_value={"status": "ok", "email": "user@gmail.com"}
        )):
            response = await client.post("/webhooks/gmail", json={
                "message": {
                    "data": encoded,
                    "messageId": "msg-test-1",
                    "publishTime": "2026-03-08T10:00:00Z"
                },
                "subscription": "projects/test/subscriptions/gmail-push"
            })
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_email_support_submission(self, client):
        """Direct email support submission should work."""
        with patch("production.api.main.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=[None, "cust-1", "conv-1", "ticket-1"])
            mock_conn.execute = AsyncMock()
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.post("/support/email", json={
                "name": "Email User",
                "email": "emailuser@gmail.com",
                "subject": "Need help",
                "message": "I need help with my account"
            })
            assert response.status_code == 200
            assert response.json()["status"] == "received"


# ============================================================
# Test Group 3: WhatsApp Channel
# ============================================================

class TestWhatsAppChannel:
    """Test WhatsApp/Meta Cloud API integration."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_verification(self, client):
        """WhatsApp webhook verification should return challenge."""
        response = await client.get("/webhooks/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "saasflow_verify_token",
            "hub.challenge": "67890"
        })
        assert response.status_code == 200
        assert response.text == "67890"

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_verification_failure(self, client):
        """Wrong verify token should fail."""
        response = await client.get("/webhooks/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "67890"
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_message(self, client):
        """WhatsApp incoming message webhook should be accepted."""
        response = await client.post("/webhooks/whatsapp", json={
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "923001234567",
                            "text": {"body": "How do I create a board?"}
                        }],
                        "contacts": [{"profile": {"name": "Ali"}}]
                    }
                }]
            }]
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mock_meta_send(self, client):
        """Mock Meta Cloud API should return valid message structure."""
        response = await client.post("/mock/meta/send", json={
            "messaging_product": "whatsapp",
            "to": "923001234567",
            "type": "text",
            "text": {"body": "Hello from test"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["messaging_product"] == "whatsapp"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["id"].startswith("wamid.mock_")

    @pytest.mark.asyncio
    async def test_mock_meta_health(self, client):
        """Mock Meta health should return ok."""
        response = await client.get("/mock/meta/health")
        assert response.status_code == 200
        assert response.json()["mock"] is True


# ============================================================
# Test Group 4: Cross-Channel Continuity
# ============================================================

class TestCrossChannelContinuity:
    """Test that conversations persist across channels."""

    @pytest.mark.asyncio
    async def test_customer_lookup_by_email(self, client):
        """Customer lookup endpoint should work."""
        with patch("production.api.main.get_db_conn", new_callable=AsyncMock) as mock_db:
            import uuid
            cust_id = uuid.uuid4()
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value={
                "id": cust_id, "email": "cross@example.com",
                "name": "Cross User", "phone": "923001234567",
                "created_at": "2026-03-08T10:00:00", "metadata": "{}"
            })
            mock_conn.fetch = AsyncMock(return_value=[
                {"id": uuid.uuid4(), "initial_channel": "web_form",
                 "status": "active", "started_at": "2026-03-08T10:00:00"},
            ])
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.get("/customers/lookup", params={"email": "cross@example.com"})
            assert response.status_code == 200
            data = response.json()
            assert len(data.get("conversations", [])) >= 1

    @pytest.mark.asyncio
    async def test_customer_lookup_not_found(self, client):
        """Missing customer should return 404."""
        with patch("production.api.main.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value=None)
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.get("/customers/lookup", params={"email": "missing@example.com"})
            assert response.status_code == 404


# ============================================================
# Test Group 5: Channel Metrics
# ============================================================

class TestChannelMetrics:
    """Test channel-specific metrics."""

    @pytest.mark.asyncio
    async def test_metrics_by_channel(self, client):
        """Should return metrics broken down by channel."""
        with patch("production.api.main.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=5)
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.get("/metrics/channels")
            assert response.status_code == 200
            data = response.json()
            for channel in ["email", "whatsapp", "web_form"]:
                assert channel in data
                assert "total_conversations" in data[channel]

    @pytest.mark.asyncio
    async def test_metrics_summary(self, client):
        """Summary metrics endpoint should work."""
        with patch("production.api.main.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value={
                "total_events": 100, "avg_latency_ms": 1.5
            })
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            response = await client.get("/metrics/summary")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Health endpoint should always return healthy."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ============================================================
# Test Group 6: Fail-Safe Ingestion (Kafka Down)
# ============================================================

class TestFailSafeIngestion:
    """Test that tickets are saved to DB when Kafka is down."""

    @pytest.mark.asyncio
    async def test_web_form_failsafe(self, client_kafka_down):
        """Web form should still accept submissions when Kafka is down."""
        with patch("production.channels.web_form_handler.get_db_conn", new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=["cust-1", "conv-1", "ticket-1"])
            mock_conn.execute = AsyncMock()
            mock_conn.close = AsyncMock()
            mock_db.return_value = mock_conn

            with patch("production.database.queries.asyncpg") as mock_pg:
                mock_pg_conn = AsyncMock()
                mock_pg_conn.fetchval = AsyncMock(return_value="pending-id-1")
                mock_pg_conn.close = AsyncMock()
                mock_pg.connect = AsyncMock(return_value=mock_pg_conn)

                response = await client_kafka_down.post("/support/submit", json={
                    "name": "Failsafe User",
                    "email": "failsafe@test.com",
                    "subject": "Kafka Down Test",
                    "category": "general",
                    "message": "Testing fail-safe when Kafka is down"
                })

                assert response.status_code == 200
                data = response.json()
                assert "ticket_id" in data
