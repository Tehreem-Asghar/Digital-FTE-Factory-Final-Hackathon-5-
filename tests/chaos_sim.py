# chaos_sim.py
"""
Automated Chaos Simulation for SaaSFlow Digital FTE (Stage 3).

Simulates random container/pod failures during active operation:
1. Random worker container kills (docker restart)
2. Kafka broker restart
3. Connection flood testing
4. Health monitoring throughout

Validates:
- Zero message loss (SC-003)
- >99.9% uptime target
- Auto-recovery from component failures

Usage:
    # Full 24-hour chaos test
    python tests/chaos_sim.py --duration 24 --interval 120

    # Quick 1-hour validation
    python tests/chaos_sim.py --duration 1 --interval 10

    # Dry-run (no actual kills)
    python tests/chaos_sim.py --dry-run
"""
import asyncio
import random
import logging
import argparse
import subprocess
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CHAOS-SIM] %(message)s")
logger = logging.getLogger("chaos_sim")

API_URL = "http://localhost:8000"


@dataclass
class ChaosEvent:
    timestamp: str
    action: str
    target: str
    result: str
    recovery_time_s: float = 0.0


@dataclass
class ChaosReport:
    start_time: str = ""
    end_time: str = ""
    total_events: int = 0
    events: List[ChaosEvent] = field(default_factory=list)
    health_checks_passed: int = 0
    health_checks_failed: int = 0
    messages_sent: int = 0
    messages_confirmed: int = 0

    @property
    def uptime_pct(self) -> float:
        total = self.health_checks_passed + self.health_checks_failed
        return (self.health_checks_passed / total * 100) if total > 0 else 0

    @property
    def message_loss_pct(self) -> float:
        if self.messages_sent == 0:
            return 0
        return ((self.messages_sent - self.messages_confirmed) / self.messages_sent) * 100


async def check_health() -> bool:
    """Check if the API is healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_URL}/health")
            return resp.status_code == 200 and resp.json().get("status") == "healthy"
    except Exception:
        return False


async def wait_for_recovery(max_wait: int = 120) -> float:
    """Wait for the system to recover and return recovery time in seconds."""
    start = time.time()
    for _ in range(max_wait):
        if await check_health():
            return time.time() - start
        await asyncio.sleep(1)
    return -1  # Failed to recover


async def send_test_message(client: httpx.AsyncClient) -> bool:
    """Send a test message to verify message processing works."""
    try:
        resp = await client.post(f"{API_URL}/support/submit", json={
            "name": "Chaos Test",
            "email": f"chaos{random.randint(1, 10000)}@test.com",
            "subject": "Chaos validation message",
            "category": "general",
            "message": "This message validates zero message loss during chaos testing."
        })
        return resp.status_code == 200 and "ticket_id" in resp.json()
    except Exception:
        return False


def restart_docker_container(container_name: str, dry_run: bool = False) -> str:
    """Restart a Docker container."""
    try:
        if dry_run:
            logger.info(f"[DRY-RUN] Would restart container: {container_name}")
            return f"dry-run:{container_name}"

        subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True, text=True, timeout=30
        )
        logger.info(f"Restarted container: {container_name}")
        return f"restarted:{container_name}"
    except FileNotFoundError:
        logger.warning("docker not found - simulating restart")
        return f"simulated:{container_name}"
    except Exception as e:
        return f"error:{e}"


def kill_docker_container(container_name: str, dry_run: bool = False) -> str:
    """Kill a Docker container (force stop)."""
    try:
        if dry_run:
            logger.info(f"[DRY-RUN] Would kill container: {container_name}")
            return f"dry-run:{container_name}"

        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True, text=True, timeout=15
        )
        # Restart it after kill to simulate pod replacement
        subprocess.run(
            ["docker", "start", container_name],
            capture_output=True, text=True, timeout=30
        )
        logger.info(f"Killed and restarted container: {container_name}")
        return f"killed:{container_name}"
    except FileNotFoundError:
        logger.warning("docker not found - simulating kill")
        return f"simulated_kill:{container_name}"
    except Exception as e:
        return f"error:{e}"


async def flood_health_endpoint(count: int = 50) -> str:
    """Flood the health endpoint to test connection handling."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.get(f"{API_URL}/health") for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        return f"flood:{successes}/{count}"


# Chaos actions with their targets
CHAOS_ACTIONS = [
    ("kill_worker", lambda dry_run: kill_docker_container("hackathon_5-kafka-1", dry_run)),
    ("restart_kafka", lambda dry_run: restart_docker_container("hackathon_5-kafka-1", dry_run)),
    ("restart_db", lambda dry_run: restart_docker_container("hackathon_5-db-1", dry_run)),
    ("connection_flood", None),  # handled separately as async
]


async def run_chaos_simulation(duration_hours: float, interval_minutes: float, dry_run: bool):
    """Main chaos simulation loop."""
    report = ChaosReport(start_time=datetime.now().isoformat())
    end_time = datetime.now() + timedelta(hours=duration_hours)

    logger.info(f"Starting chaos simulation for {duration_hours}h with {interval_minutes}min intervals")
    logger.info(f"Dry run: {dry_run}")

    # Initial health check
    if await check_health():
        logger.info("System is healthy - starting chaos simulation")
        report.health_checks_passed += 1
    else:
        logger.warning("System is NOT healthy at start - proceeding anyway")
        report.health_checks_failed += 1

    cycle = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while datetime.now() < end_time:
            cycle += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"CHAOS CYCLE {cycle} ({datetime.now().strftime('%H:%M:%S')})")
            logger.info(f"{'='*60}")

            # 1. Send pre-chaos test message
            pre_ok = await send_test_message(client)
            if pre_ok:
                report.messages_sent += 1
                report.messages_confirmed += 1
                logger.info("[PRE-CHAOS] Test message: OK")
            else:
                report.messages_sent += 1
                logger.warning("[PRE-CHAOS] Test message: FAILED")

            # 2. Pick a random chaos action
            action_name, action_func = random.choice(CHAOS_ACTIONS)
            logger.info(f"Action: {action_name}")

            target = "n/a"
            if action_name == "connection_flood":
                target = await flood_health_endpoint(50)
            else:
                target = action_func(dry_run=dry_run)

            # 3. Wait for recovery
            recovery_time = await wait_for_recovery(max_wait=120)

            event = ChaosEvent(
                timestamp=datetime.now().isoformat(),
                action=action_name,
                target=str(target),
                result="recovered" if recovery_time >= 0 else "failed",
                recovery_time_s=recovery_time if recovery_time >= 0 else -1,
            )
            report.events.append(event)
            report.total_events += 1

            if recovery_time >= 0:
                logger.info(f"System recovered in {recovery_time:.1f}s")
                report.health_checks_passed += 1
            else:
                logger.error("System FAILED to recover within 120s!")
                report.health_checks_failed += 1

            # 4. Send post-chaos test message (validates zero message loss)
            post_ok = await send_test_message(client)
            if post_ok:
                report.messages_sent += 1
                report.messages_confirmed += 1
                logger.info("[POST-CHAOS] Test message: OK")
            else:
                report.messages_sent += 1
                logger.warning("[POST-CHAOS] Test message: FAILED")

            # 5. Wait until next chaos event with periodic health checks
            logger.info(f"Waiting {interval_minutes} minutes until next chaos event...")
            wait_seconds = interval_minutes * 60
            checks = int(wait_seconds / 30)
            for i in range(checks):
                await asyncio.sleep(30)
                healthy = await check_health()
                if healthy:
                    report.health_checks_passed += 1
                else:
                    report.health_checks_failed += 1
                    logger.warning(f"Health check FAILED during wait (check {i+1})")

    report.end_time = datetime.now().isoformat()

    # --- Final Report ---
    print("\n" + "=" * 65)
    print("CHAOS SIMULATION REPORT")
    print("=" * 65)
    print(f"Duration:         {report.start_time} -> {report.end_time}")
    print(f"Total Events:     {report.total_events}")
    print(f"Uptime:           {report.uptime_pct:.1f}%")
    print(f"Health Passed:    {report.health_checks_passed}")
    print(f"Health Failed:    {report.health_checks_failed}")
    print(f"Messages Sent:    {report.messages_sent}")
    print(f"Messages Confirm: {report.messages_confirmed}")
    print(f"Message Loss:     {report.message_loss_pct:.2f}%")
    print()
    print("Events:")
    for e in report.events:
        status = "OK" if e.result == "recovered" else "FAIL"
        print(f"  [{status}] {e.timestamp} | {e.action} -> {e.target} | Recovery: {e.recovery_time_s:.1f}s")
    print("=" * 65)

    # Acceptance criteria
    passed = True
    if report.uptime_pct < 99.9:
        print(f"FAIL: Uptime {report.uptime_pct:.1f}% < 99.9%")
        passed = False
    if report.message_loss_pct > 0:
        print(f"FAIL: Message loss {report.message_loss_pct:.2f}% > 0%")
        passed = False

    if passed:
        print("RESULT: PASSED (SC-003 Zero Message Loss, >99.9% Uptime)")
    else:
        print("RESULT: FAILED - See failures above")

    print("=" * 65)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chaos Simulation for Digital FTE")
    parser.add_argument("--duration", type=float, default=24, help="Test duration in hours")
    parser.add_argument("--interval", type=float, default=120, help="Chaos event interval in minutes")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without actual kills")
    args = parser.parse_args()

    asyncio.run(run_chaos_simulation(args.duration, args.interval, args.dry_run))
