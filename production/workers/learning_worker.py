# learning_worker.py
# Learn from Resolved Tickets - Extracts patterns from resolved tickets
# and adds them to the knowledge base for improved future responses.

import asyncio
import json
import logging
import os
import re
import httpx
from datetime import datetime
from production.agent.tools import get_db_conn, get_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("api_key")


def _get_active_key():
    try:
        from production.agent.customer_success_agent import get_current_api_key
        return get_current_api_key()
    except ImportError:
        return GEMINI_API_KEY


async def extract_resolution_summary(messages: list) -> dict:
    """Extract issue summary and resolution from conversation messages using Gemini."""
    # Build conversation text
    conversation = "\n".join(
        f"[{m['role']}] ({m['channel']}): {m['content']}" for m in messages
    )

    prompt = (
        "Analyze this support conversation and extract:\n"
        "1. issue_summary: One sentence describing the customer's problem\n"
        "2. resolution_summary: One sentence describing how it was resolved\n"
        "3. issue_category: One of: billing, technical, how_to, bug_report, feedback, account, general\n"
        "4. keywords: 3-5 relevant keywords as a comma-separated list\n\n"
        f"Conversation:\n{conversation}\n\n"
        "Return ONLY valid JSON with keys: issue_summary, resolution_summary, issue_category, keywords"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={_get_active_key()}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300}
            }
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Clean markdown code fences if present
                text = re.sub(r'^```json\s*', '', text)
                text = re.sub(r'\s*```$', '', text)
                return json.loads(text)
    except Exception as e:
        logger.warning(f"Gemini extraction failed: {e}")

    # Fallback: basic extraction from first/last messages
    customer_msgs = [m for m in messages if m["role"] == "customer"]
    agent_msgs = [m for m in messages if m["role"] == "agent"]
    return {
        "issue_summary": customer_msgs[0]["content"][:200] if customer_msgs else "Unknown issue",
        "resolution_summary": agent_msgs[-1]["content"][:200] if agent_msgs else "Resolved by agent",
        "issue_category": "general",
        "keywords": "support,customer,resolved"
    }


async def process_resolved_tickets():
    """Scan for resolved tickets that haven't been processed for learnings yet."""
    conn = await get_db_conn()
    try:
        # Find resolved tickets not yet in resolution_learnings
        resolved = await conn.fetch("""
            SELECT t.id as ticket_id, t.conversation_id, t.source_channel, t.category,
                   t.created_at as ticket_created, t.resolved_at,
                   (SELECT COUNT(*) FROM resolution_learnings rl WHERE rl.ticket_id = t.id) as already_learned
            FROM tickets t
            WHERE t.status IN ('resolved', 'closed')
              AND t.conversation_id IS NOT NULL
            ORDER BY t.resolved_at DESC NULLS LAST
            LIMIT 20
        """)

        new_learnings = 0
        for ticket in resolved:
            if ticket["already_learned"] > 0:
                continue

            # Get conversation messages
            messages = await conn.fetch("""
                SELECT role, content, channel, direction, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
            """, ticket["conversation_id"])

            if len(messages) < 2:
                continue

            msg_list = [dict(m) for m in messages]

            # Extract learnings using AI
            learning = await extract_resolution_summary(msg_list)

            # Calculate resolution time
            resolution_hours = None
            if ticket["resolved_at"] and ticket["ticket_created"]:
                delta = ticket["resolved_at"] - ticket["ticket_created"]
                resolution_hours = round(delta.total_seconds() / 3600, 2)

            # Parse keywords
            keywords_str = learning.get("keywords", "")
            if isinstance(keywords_str, str):
                keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            else:
                keywords = keywords_str

            # Check if ticket was escalated
            was_escalated = await conn.fetchval(
                "SELECT COUNT(*) > 0 FROM agent_metrics WHERE metric_name = 'escalation' AND dimensions->>'ticket_id' = $1",
                str(ticket["ticket_id"])
            )

            # Generate embedding for the learning
            embedding = None
            try:
                embed_text = f"{learning.get('issue_summary', '')} {learning.get('resolution_summary', '')}"
                embedding = await get_embedding(embed_text)
            except Exception as e:
                logger.warning(f"Embedding generation failed for ticket {ticket['ticket_id']}: {e}")

            # Store the learning
            vector_str = f"[{','.join(map(str, embedding))}]" if embedding else None
            await conn.execute("""
                INSERT INTO resolution_learnings
                    (ticket_id, issue_category, issue_summary, resolution_summary,
                     source_channel, resolution_time_hours, was_escalated, keywords, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                ticket["ticket_id"],
                learning.get("issue_category", ticket.get("category", "general")),
                learning.get("issue_summary", ""),
                learning.get("resolution_summary", ""),
                ticket["source_channel"],
                resolution_hours,
                was_escalated or False,
                keywords,
                vector_str
            )

            new_learnings += 1
            logger.info(f"Learned from ticket {ticket['ticket_id']}: {learning.get('issue_category')}")

        return new_learnings

    finally:
        await conn.close()


async def get_similar_resolutions(query: str, limit: int = 3) -> list:
    """Find similar past resolutions using semantic search on learnings."""
    conn = await get_db_conn()
    try:
        try:
            query_vector = await get_embedding(query)
            vector_str = f"[{','.join(map(str, query_vector))}]"
            rows = await conn.fetch("""
                SELECT issue_summary, resolution_summary, issue_category,
                       source_channel, keywords, 1 - (embedding <=> $1) as similarity
                FROM resolution_learnings
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1
                LIMIT $2
            """, vector_str, limit)
            return [dict(r) for r in rows]
        except Exception:
            # Fallback: keyword search
            words = [f"%{w}%" for w in query.split() if len(w) > 3]
            if not words:
                return []
            rows = await conn.fetch("""
                SELECT issue_summary, resolution_summary, issue_category, source_channel, keywords
                FROM resolution_learnings
                WHERE issue_summary ILIKE ANY($1) OR resolution_summary ILIKE ANY($1)
                LIMIT $2
            """, words, limit)
            return [dict(r) for r in rows]
    finally:
        await conn.close()


async def run_learning_cycle():
    """Run the learning worker in a loop."""
    logger.info("Learning Worker started - processing resolved tickets...")
    while True:
        try:
            count = await process_resolved_tickets()
            if count > 0:
                logger.info(f"Extracted {count} new learnings from resolved tickets.")
            else:
                logger.debug("No new resolved tickets to learn from.")
        except Exception as e:
            logger.error(f"Learning cycle error: {e}")

        await asyncio.sleep(60)  # Check every 60 seconds


if __name__ == "__main__":
    asyncio.run(run_learning_cycle())
