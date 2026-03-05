# locustfile.py
"""
Locust Load Testing for SaaSFlow Digital FTE API.

Usage:
    locust -f production/tests/locustfile.py --host http://localhost:8000

Targets:
    - Health endpoint (baseline)
    - Web form submission (main load)
    - WhatsApp webhook verification
    - Gmail webhook notification
    - Metrics endpoints
"""
import json
import random
import base64
from locust import HttpUser, task, between, tag


# Sample test data
SAMPLE_EMAILS = [
    f"user{i}@test.com" for i in range(100)
]

SAMPLE_ISSUES = [
    "How do I create a new board?",
    "Cannot login to my account",
    "How to invite team members?",
    "Automation not working properly",
    "Need help with Slack integration",
    "How to export my data?",
    "Card drag and drop broken on mobile",
    "Upgrade from Free to Pro plan",
    "GitHub integration setup help",
    "Password reset link expired",
    "How do I set up workflow automations?",
    "Board loading very slowly",
    "Cannot see my team members' cards",
    "Integration with Google Drive not syncing",
    "Need to change my email address",
]

SAMPLE_NAMES = ["Ali", "Sara", "Ahmed", "Fatima", "Omar", "Hira", "Zain", "Aisha"]


class DigitalFTEUser(HttpUser):
    """Simulates a realistic traffic pattern across all API endpoints."""
    wait_time = between(1, 5)  # 1-5 seconds between requests

    @tag("health")
    @task(1)
    def health_check(self):
        """Baseline: health endpoint should always respond fast."""
        self.client.get("/health")

    @tag("web_form")
    @task(5)
    def submit_web_form(self):
        """Primary load: web form submissions."""
        payload = {
            "name": random.choice(SAMPLE_NAMES),
            "email": random.choice(SAMPLE_EMAILS),
            "subject": random.choice(SAMPLE_ISSUES)[:50],
            "message": random.choice(SAMPLE_ISSUES),
            "channel": "web_form",
        }
        self.client.post("/support/submit", json=payload)

    @tag("whatsapp")
    @task(3)
    def whatsapp_webhook(self):
        """Simulates incoming WhatsApp messages."""
        payload = {
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
        }
        self.client.post("/webhooks/whatsapp", json=payload)

    @tag("gmail")
    @task(2)
    def gmail_webhook(self):
        """Simulates Gmail Pub/Sub notifications."""
        email = random.choice(SAMPLE_EMAILS)
        notification = base64.b64encode(
            json.dumps({
                "emailAddress": email,
                "historyId": str(random.randint(10000, 99999)),
            }).encode()
        ).decode()

        payload = {
            "message": {
                "data": notification,
                "messageId": f"msg-{random.randint(1000, 9999)}",
                "publishTime": "2026-03-04T10:00:00Z",
            },
            "subscription": "projects/saasflow-fte/subscriptions/gmail-push",
        }
        self.client.post("/webhooks/gmail", json=payload)

    @tag("metrics")
    @task(1)
    def check_metrics(self):
        """Periodically query metrics endpoints."""
        self.client.get("/metrics/channels")

    @tag("metrics")
    @task(1)
    def check_summary(self):
        """Periodically query summary endpoint."""
        self.client.get("/metrics/summary")

    @tag("whatsapp_verify")
    @task(1)
    def whatsapp_verify(self):
        """Simulates WhatsApp webhook verification."""
        self.client.get("/webhooks/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "saasflow_verify_token",
            "hub.challenge": str(random.randint(10000, 99999)),
        })


class SpikeUser(HttpUser):
    """Simulates traffic spike - aggressive user with no wait time."""
    wait_time = between(0.1, 0.5)
    weight = 1  # Less common than normal users

    @task
    def rapid_submit(self):
        """Rapid-fire form submissions to test backpressure."""
        payload = {
            "name": "Spike Test",
            "email": f"spike{random.randint(1, 1000)}@test.com",
            "subject": "Load test",
            "message": random.choice(SAMPLE_ISSUES),
            "channel": "web_form",
        }
        self.client.post("/support/submit", json=payload)
