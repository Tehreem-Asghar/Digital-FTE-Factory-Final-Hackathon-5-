# multichannel_test.py
"""
24-Hour Multi-Channel Test Validator for SaaSFlow Digital FTE.

Simulates a full 24-hour test by sending messages across all 3 channels
(Email, WhatsApp, Web Form) at realistic intervals and collecting metrics.

Usage:
    # Full 24-hour test
    python -m production.tests.multichannel_test --duration 24

    # Quick 1-hour validation
    python -m production.tests.multichannel_test --duration 1

    # Dry-run (just prints what would happen)
    python -m production.tests.multichannel_test --dry-run
"""
import asyncio
import random
import json
import base64
import logging
import argparse
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MULTITEST] %(message)s")
logger = logging.getLogger("multichannel_test")

API_URL = "http://localhost:8000"

# ============================================================
# Test Scenarios - Covers all edge cases from discovery-log.md
# ============================================================

WEB_FORM_SCENARIOS = [
    {"name": "Alice Johnson", "email": "alice@company.com", "subject": "Board Setup Help", "message": "Hi, I just signed up and I'm trying to create my first Kanban board. Can you walk me through the steps?"},
    {"name": "Bob Smith", "email": "bob@startup.io", "subject": "Automation Not Working", "message": "I set up an automation to notify Slack when a card moves but it's not triggering. I'm on the Starter plan."},
    {"name": "Carol Lee", "email": "carol@enterprise.co", "subject": "Team Invite Issue", "message": "I'm an admin and I invited 3 team members but they haven't received the invitation email. It's been 2 hours."},
    {"name": "Dave Park", "email": "dave@test.com", "subject": "Data Export", "message": "I need to export all my boards as CSV for a report. Is that possible?"},
    {"name": "Eve Wilson", "email": "eve@test.com", "subject": "Refund Request", "message": "I was charged twice for my Pro subscription. I need a refund immediately."},
    {"name": "Frank Chen", "email": "frank@angry.com", "subject": "Terrible Service", "message": "This is absolutely ridiculous! Your app keeps crashing and I've lost all my work. I want to talk to a manager NOW!"},
    {"name": "Grace Kim", "email": "grace@legal.com", "subject": "Legal Question", "message": "I need to understand your data retention policies. Our lawyers need this for compliance review."},
    {"name": "Hank Brown", "email": "hank@test.com", "subject": "GitHub Integration", "message": "How do I connect my GitHub repository to Kanbix? I'm on the Pro plan."},
]

WHATSAPP_SCENARIOS = [
    {"from": "923001111111", "body": "How do I create a board?", "name": "Ali"},
    {"from": "923002222222", "body": "My cards are not loading", "name": "Sara"},
    {"from": "923003333333", "body": "What plans do you have?", "name": "Ahmed"},
    {"from": "923004444444", "body": "I want a refund", "name": "Fatima"},
    {"from": "923005555555", "body": "Connect me to a human agent please", "name": "Omar"},
    {"from": "923006666666", "body": "How to set up Slack integration?", "name": "Hira"},
    {"from": "923007777777", "body": "Password reset not working", "name": "Zain"},
    {"from": "923008888888", "body": "I'm going to sue you if this isn't fixed", "name": "Test Legal"},
]

EMAIL_SCENARIOS = [
    {"email": "user1@gmail.com", "historyId": "10001"},
    {"email": "user2@gmail.com", "historyId": "10002"},
    {"email": "user3@outlook.com", "historyId": "10003"},
    {"email": "user4@company.com", "historyId": "10004"},
    {"email": "user5@enterprise.io", "historyId": "10005"},
]


@dataclass
class TestResult:
    channel: str
    scenario: str
    status_code: int
    response_time_ms: float
    success: bool
    timestamp: str
    error: str = ""


@dataclass
class MultiChannelReport:
    start_time: str = ""
    end_time: str = ""
    duration_hours: float = 0
    results: List[TestResult] = field(default_factory=list)

    @property
    def total_requests(self) -> int:
        return len(self.results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def success_rate(self) -> float:
        return (self.success_count / self.total_requests * 100) if self.total_requests > 0 else 0

    @property
    def avg_response_time(self) -> float:
        times = [r.response_time_ms for r in self.results if r.success]
        return sum(times) / len(times) if times else 0

    @property
    def p95_response_time(self) -> float:
        times = sorted([r.response_time_ms for r in self.results if r.success])
        if not times:
            return 0
        idx = int(len(times) * 0.95)
        return times[min(idx, len(times) - 1)]

    def by_channel(self) -> Dict[str, List[TestResult]]:
        channels: Dict[str, List[TestResult]] = {}
        for r in self.results:
            channels.setdefault(r.channel, []).append(r)
        return channels


async def send_web_form(client: httpx.AsyncClient, scenario: dict) -> TestResult:
    """Sends a web form submission."""
    start = time.time()
    try:
        resp = await client.post(f"{API_URL}/support/submit", json={
            "name": scenario["name"],
            "email": scenario["email"],
            "subject": scenario["subject"],
            "message": scenario["message"],
            "channel": "web_form",
        })
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="web_form",
            scenario=scenario["subject"],
            status_code=resp.status_code,
            response_time_ms=elapsed,
            success=resp.status_code == 200,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="web_form", scenario=scenario["subject"],
            status_code=0, response_time_ms=elapsed,
            success=False, timestamp=datetime.now().isoformat(), error=str(e),
        )


async def send_whatsapp(client: httpx.AsyncClient, scenario: dict) -> TestResult:
    """Sends a simulated WhatsApp webhook."""
    start = time.time()
    try:
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": scenario["from"],
                            "text": {"body": scenario["body"]},
                        }],
                        "contacts": [{"profile": {"name": scenario["name"]}}],
                    }
                }]
            }]
        }
        resp = await client.post(f"{API_URL}/webhooks/whatsapp", json=payload)
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="whatsapp",
            scenario=scenario["body"][:40],
            status_code=resp.status_code,
            response_time_ms=elapsed,
            success=resp.status_code == 200,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="whatsapp", scenario=scenario["body"][:40],
            status_code=0, response_time_ms=elapsed,
            success=False, timestamp=datetime.now().isoformat(), error=str(e),
        )


async def send_gmail(client: httpx.AsyncClient, scenario: dict) -> TestResult:
    """Sends a simulated Gmail Pub/Sub notification."""
    start = time.time()
    try:
        encoded = base64.b64encode(json.dumps({
            "emailAddress": scenario["email"],
            "historyId": scenario["historyId"],
        }).encode()).decode()

        payload = {
            "message": {
                "data": encoded,
                "messageId": f"msg-{random.randint(1000, 9999)}",
                "publishTime": datetime.now().isoformat(),
            },
            "subscription": "projects/saasflow-fte/subscriptions/gmail-push",
        }
        resp = await client.post(f"{API_URL}/webhooks/gmail", json=payload)
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="email",
            scenario=scenario["email"],
            status_code=resp.status_code,
            response_time_ms=elapsed,
            success=resp.status_code == 200,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return TestResult(
            channel="email", scenario=scenario["email"],
            status_code=0, response_time_ms=elapsed,
            success=False, timestamp=datetime.now().isoformat(), error=str(e),
        )


async def run_multichannel_test(duration_hours: float, dry_run: bool):
    """Main 24-hour multi-channel test runner."""
    report = MultiChannelReport(
        start_time=datetime.now().isoformat(),
        duration_hours=duration_hours,
    )
    end_time = datetime.now() + timedelta(hours=duration_hours)

    logger.info(f"Starting {duration_hours}-hour multi-channel test")
    logger.info(f"Dry run: {dry_run}")

    # Check health first
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{API_URL}/health")
            if resp.status_code == 200:
                logger.info("API is healthy - starting test")
            else:
                logger.warning("API returned non-200 - proceeding anyway")
        except Exception as e:
            logger.error(f"Cannot reach API at {API_URL}: {e}")
            if not dry_run:
                logger.error("Aborting test. Start the API first: uvicorn production.api.main:app")
                return report

    cycle = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while datetime.now() < end_time:
            cycle += 1
            logger.info(f"\n--- Cycle {cycle} ({datetime.now().strftime('%H:%M:%S')}) ---")

            # Pick random scenarios from each channel
            web_scenario = random.choice(WEB_FORM_SCENARIOS)
            wa_scenario = random.choice(WHATSAPP_SCENARIOS)
            email_scenario = random.choice(EMAIL_SCENARIOS)

            if dry_run:
                logger.info(f"  [DRY] Web Form: {web_scenario['subject']}")
                logger.info(f"  [DRY] WhatsApp: {wa_scenario['body'][:40]}")
                logger.info(f"  [DRY] Email:    {email_scenario['email']}")
            else:
                # Send all 3 channels concurrently
                results = await asyncio.gather(
                    send_web_form(client, web_scenario),
                    send_whatsapp(client, wa_scenario),
                    send_gmail(client, email_scenario),
                    return_exceptions=True,
                )

                for r in results:
                    if isinstance(r, TestResult):
                        report.results.append(r)
                        status = "OK" if r.success else "FAIL"
                        logger.info(f"  [{status}] {r.channel}: {r.scenario} ({r.response_time_ms:.0f}ms)")
                    else:
                        logger.error(f"  [ERROR] {r}")

            # Wait between cycles (realistic interval: ~30s between message bursts)
            wait_time = random.uniform(15, 45)
            await asyncio.sleep(wait_time)

    report.end_time = datetime.now().isoformat()

    # Print final report
    print("\n" + "=" * 70)
    print("24-HOUR MULTI-CHANNEL TEST REPORT")
    print("=" * 70)
    print(f"Duration:         {report.duration_hours}h ({report.start_time} -> {report.end_time})")
    print(f"Total Requests:   {report.total_requests}")
    print(f"Success Rate:     {report.success_rate:.1f}%")
    print(f"Avg Response:     {report.avg_response_time:.0f}ms")
    print(f"P95 Response:     {report.p95_response_time:.0f}ms")
    print()

    print("Per-Channel Breakdown:")
    for ch, ch_results in report.by_channel().items():
        successes = sum(1 for r in ch_results if r.success)
        times = [r.response_time_ms for r in ch_results if r.success]
        avg_time = sum(times) / len(times) if times else 0
        print(f"  {ch:12s}: {successes}/{len(ch_results)} passed | Avg: {avg_time:.0f}ms")

    print()

    # Check acceptance criteria
    passed = True
    if report.success_rate < 99.9:
        print(f"FAIL: Success rate {report.success_rate:.1f}% < 99.9%")
        passed = False
    if report.p95_response_time > 3000:
        print(f"FAIL: P95 latency {report.p95_response_time:.0f}ms > 3000ms")
        passed = False

    if passed:
        print("RESULT: PASSED - All acceptance criteria met")
    else:
        print("RESULT: FAILED - See failures above")

    print("=" * 70)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="24-Hour Multi-Channel Test")
    parser.add_argument("--duration", type=float, default=24, help="Test duration in hours")
    parser.add_argument("--dry-run", action="store_true", help="Print scenarios without sending")
    args = parser.parse_args()

    asyncio.run(run_multichannel_test(args.duration, args.dry_run))
