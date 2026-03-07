# load_test.py
"""
Locust Load Testing for SaaSFlow Digital FTE API (Stage 3).

Simulates 100+ concurrent users across all channels:
- Web Form submissions (most common, weight=3)
- WhatsApp webhook messages (weight=2)
- Gmail webhook notifications (weight=1)
- Health check monitoring (weight=1)

Usage:
    locust -f tests/load_test.py --host http://localhost:8000

    # Quick test (30 users, 60 seconds)
    locust -f tests/load_test.py --host http://localhost:8000 --users 30 --spawn-rate 5 --run-time 60s --headless

    # Full stress test (100+ users)
    locust -f tests/load_test.py --host http://localhost:8000 --users 150 --spawn-rate 10 --run-time 300s --headless
"""
import json
import random
import base64
from locust import HttpUser, task, between, tag, events
from datetime import datetime


# --- Test Data ---

SAMPLE_NAMES = ["Ali", "Sara", "Ahmed", "Fatima", "Omar", "Hira", "Zain", "Aisha",
                "Bob", "Alice", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank"]

SAMPLE_EMAILS = [f"loaduser{i}@example.com" for i in range(200)]

SAMPLE_ISSUES = [
    "How do I create a new board?",
    "Cannot login to my account",
    "How to invite team members?",
    "Automation not working properly",
    "Need help with Slack integration",
    "How to export my data as CSV?",
    "Card drag and drop broken on mobile",
    "Upgrade from Free to Pro plan",
    "GitHub integration setup help",
    "Password reset link expired",
    "How do I set up workflow automations?",
    "Board loading very slowly",
    "Cannot see my team members' cards",
    "Integration with Google Drive not syncing",
    "Need to change my email address",
    "How to archive a board?",
    "Custom fields not saving properly",
    "API rate limits exceeded",
    "Two-factor authentication setup",
    "Webhook delivery failing",
]

CATEGORIES = ["general", "technical", "billing", "feedback", "bug_report"]


# --- User Classes ---

class WebFormUser(HttpUser):
    """Simulate users submitting support forms (most common traffic)."""
    wait_time = between(2, 10)
    weight = 3

    @tag("web_form")
    @task(5)
    def submit_support_form(self):
        """Submit a web form ticket."""
        self.client.post("/support/submit", json={
            "name": random.choice(SAMPLE_NAMES),
            "email": random.choice(SAMPLE_EMAILS),
            "subject": random.choice(SAMPLE_ISSUES)[:50],
            "category": random.choice(CATEGORIES),
            "message": random.choice(SAMPLE_ISSUES),
        })

    @tag("health")
    @task(1)
    def check_health(self):
        """Baseline health check."""
        self.client.get("/health")

    @tag("metrics")
    @task(1)
    def check_metrics(self):
        """Periodically check metrics endpoint."""
        self.client.get("/metrics/summary")

    @tag("metrics")
    @task(1)
    def check_channel_metrics(self):
        """Check per-channel metrics."""
        self.client.get("/metrics/channels")


class WhatsAppUser(HttpUser):
    """Simulate incoming WhatsApp messages."""
    wait_time = between(3, 12)
    weight = 2

    @tag("whatsapp")
    @task
    def send_whatsapp_message(self):
        """Simulate Meta Cloud API webhook delivery."""
        self.client.post("/webhooks/whatsapp", json={
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": f"9230{random.randint(10000000, 99999999)}",
                            "text": {"body": random.choice(SAMPLE_ISSUES)},
                        }],
                        "contacts": [{
                            "profile": {"name": random.choice(SAMPLE_NAMES)}
                        }],
                    }
                }]
            }]
        })


class EmailUser(HttpUser):
    """Simulate Gmail Pub/Sub notifications."""
    wait_time = between(5, 15)
    weight = 1

    @tag("gmail")
    @task
    def send_gmail_notification(self):
        """Simulate Gmail Pub/Sub push notification."""
        email = random.choice(SAMPLE_EMAILS)
        notification = base64.b64encode(
            json.dumps({
                "emailAddress": email,
                "historyId": str(random.randint(10000, 99999)),
            }).encode()
        ).decode()

        self.client.post("/webhooks/gmail", json={
            "message": {
                "data": notification,
                "messageId": f"msg-{random.randint(1000, 9999)}",
                "publishTime": datetime.now().isoformat() + "Z",
            },
            "subscription": "projects/saasflow-fte/subscriptions/gmail-push",
        })


class HealthCheckUser(HttpUser):
    """Monitor system health during load test."""
    wait_time = between(5, 15)
    weight = 1

    @tag("health")
    @task
    def check_health(self):
        """Continuous health monitoring."""
        self.client.get("/health")

    @tag("whatsapp_verify")
    @task
    def whatsapp_verify(self):
        """Verify WhatsApp webhook (lightweight check)."""
        self.client.get("/webhooks/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "saasflow_verify_token",
            "hub.challenge": str(random.randint(10000, 99999)),
        })


class SpikeUser(HttpUser):
    """Simulates traffic spike - aggressive user with minimal wait time."""
    wait_time = between(0.1, 0.5)
    weight = 1

    @tag("spike")
    @task
    def rapid_submit(self):
        """Rapid-fire form submissions to test backpressure."""
        self.client.post("/support/submit", json={
            "name": "Spike Test",
            "email": f"spike{random.randint(1, 1000)}@test.com",
            "subject": "Load test spike",
            "category": "general",
            "message": random.choice(SAMPLE_ISSUES),
        })
