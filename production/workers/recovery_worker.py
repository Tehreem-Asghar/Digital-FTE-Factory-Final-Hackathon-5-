# recovery_worker.py
"""
Background recovery worker that drains the pending_ingestion DB table
into Kafka once the broker is healthy again.

Usage:
    python -m production.workers.recovery_worker

    # Custom interval (default 30s):
    python -m production.workers.recovery_worker --interval 15
"""
import asyncio
import json
import logging
import argparse
from production.utils.kafka_client import FTEKafkaProducer
from production.database.queries import (
    get_pending_messages,
    mark_pending_published,
    increment_pending_retry,
    mark_pending_failed,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [RECOVERY] %(message)s")
logger = logging.getLogger("recovery_worker")

MAX_RETRIES = 5


class RecoveryWorker:
    """Polls pending_ingestion table and pushes messages to Kafka."""

    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self.producer = FTEKafkaProducer()
        self.running = True

    async def start(self):
        """Main loop: check Kafka health, then drain pending messages."""
        logger.info(f"Recovery worker started (poll every {self.poll_interval}s)")

        while self.running:
            try:
                # 1. Check if Kafka is healthy
                kafka_healthy = await self.producer.health_check()

                if not kafka_healthy:
                    logger.warning("Kafka is unreachable. Waiting for recovery...")
                    await asyncio.sleep(self.poll_interval)
                    continue

                # 2. Ensure producer is started
                if not self.producer.producer:
                    await self.producer.start()

                # 3. Fetch pending messages
                pending = await get_pending_messages(limit=50)

                if not pending:
                    await asyncio.sleep(self.poll_interval)
                    continue

                logger.info(f"Found {len(pending)} pending messages to publish")

                # 4. Publish each to Kafka
                published = 0
                for msg in pending:
                    msg_id = msg["id"]
                    topic = msg["topic"]
                    payload = msg["payload"]
                    retry_count = msg["retry_count"]

                    # Parse payload if it's a string
                    if isinstance(payload, str):
                        payload = json.loads(payload)

                    try:
                        await self.producer.publish(topic, payload)
                        await mark_pending_published(str(msg_id))
                        published += 1
                    except Exception as e:
                        logger.error(f"Failed to publish msg {msg_id}: {e}")
                        if retry_count + 1 >= MAX_RETRIES:
                            await mark_pending_failed(str(msg_id))
                            logger.error(f"Message {msg_id} permanently failed after {MAX_RETRIES} retries")
                        else:
                            await increment_pending_retry(str(msg_id))

                logger.info(f"Published {published}/{len(pending)} pending messages")

            except Exception as e:
                logger.error(f"Recovery worker error: {e}")

            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Graceful shutdown."""
        self.running = False
        await self.producer.stop()
        logger.info("Recovery worker stopped")


async def main(interval: int):
    worker = RecoveryWorker(poll_interval=interval)
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Recovery Worker")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    args = parser.parse_args()
    asyncio.run(main(args.interval))
