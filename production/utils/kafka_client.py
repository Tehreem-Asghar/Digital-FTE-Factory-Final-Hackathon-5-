# kafka_client.py
import os
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

class FTEKafkaConsumer:
    def __init__(self, topics: list, group_id: str):
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()

    async def consume(self, handler_func):
        """Infinite loop to consume messages and call the handler function."""
        async for msg in self.consumer:
            await handler_func(msg.topic, msg.value)

class FTEKafkaProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, message: dict):
        if not self.producer:
            await self.start()
        message["timestamp"] = datetime.now().isoformat()
        await self.producer.send_and_wait(topic, message)
