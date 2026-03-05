# metrics_collector.py
import asyncio
import logging
from production.utils.kafka_client import FTEKafkaConsumer
from production.agent.tools import get_db_conn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Consumes metrics events and stores them in PostgreSQL."""
    
    def __init__(self):
        self.consumer = None

    async def start(self):
        self.consumer = FTEKafkaConsumer(
            topics=["fte.metrics"],
            group_id="metrics-collector"
        )
        await self.consumer.start()
        logger.info("Metrics collector started, listening for events...")
        await self.consumer.consume(self.process_metrics)

    async def process_metrics(self, topic: str, data: dict):
        """Saves a metric event to the database."""
        conn = await get_db_conn()
        try:
            metric_name = data.get("event_type", "unknown")
            metric_value = data.get("latency_ms", 0.0)
            channel = data.get("channel")
            
            await conn.execute(
                "INSERT INTO agent_metrics (metric_name, metric_value, channel) VALUES ($1, $2, $3)",
                metric_name, float(metric_value), channel
            )
            logger.info(f"Recorded metric: {metric_name} for channel {channel}")
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
        finally:
            await conn.close()

if __name__ == "__main__":
    collector = MetricsCollector()
    asyncio.run(collector.start())
