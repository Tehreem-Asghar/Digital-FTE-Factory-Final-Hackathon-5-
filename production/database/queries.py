# queries.py
import asyncpg
from typing import List, Dict, Any
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5433/fte_db")

async def get_customer_by_email(email: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        return await conn.fetchrow("SELECT * FROM customers WHERE email = $1", email)
    finally:
        await conn.close()

async def get_recent_messages(conversation_id: str, limit: int = 10):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        return await conn.fetch(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2",
            conversation_id, limit
        )
    finally:
        await conn.close()

async def update_ticket_status(ticket_id: str, status: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("UPDATE tickets SET status = $1 WHERE id = $2", status, ticket_id)
    finally:
        await conn.close()


# --- Fail-Safe Ingestion (pending_ingestion) ---

async def save_pending_message(topic: str, payload: dict) -> str:
    """Save a message to pending_ingestion when Kafka is unavailable."""
    import json
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row_id = await conn.fetchval(
            "INSERT INTO pending_ingestion (topic, payload, status) "
            "VALUES ($1, $2::jsonb, 'pending') RETURNING id",
            topic, json.dumps(payload)
        )
        return str(row_id)
    finally:
        await conn.close()


async def get_pending_messages(limit: int = 50) -> list:
    """Fetch pending messages that need to be published to Kafka."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT id, topic, payload, retry_count FROM pending_ingestion "
            "WHERE status = 'pending' AND retry_count < 5 "
            "ORDER BY created_at ASC LIMIT $1",
            limit
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def mark_pending_published(msg_id: str):
    """Mark a pending message as successfully published to Kafka."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE pending_ingestion SET status = 'published', published_at = NOW() "
            "WHERE id = $1",
            msg_id
        )
    finally:
        await conn.close()


async def increment_pending_retry(msg_id: str):
    """Increment retry count for a failed pending message."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE pending_ingestion SET retry_count = retry_count + 1 WHERE id = $1",
            msg_id
        )
    finally:
        await conn.close()


async def mark_pending_failed(msg_id: str):
    """Mark a pending message as permanently failed (max retries exceeded)."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE pending_ingestion SET status = 'failed' WHERE id = $1",
            msg_id
        )
    finally:
        await conn.close()
