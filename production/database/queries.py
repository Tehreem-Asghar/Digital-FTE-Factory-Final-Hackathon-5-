# queries.py
import asyncpg
from typing import List, Dict, Any
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5432/fte_db")

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
