# seed_kb.py
"""Seeds the knowledge base with product documentation and Gemini embeddings."""
import asyncio
import os
import httpx
from dotenv import load_dotenv
from production.agent.tools import get_db_conn

load_dotenv()

GEMINI_API_KEY = os.getenv("api_key")

# Detailed samples from the new Product Docs
SAMPLE_DOCS = [
    {"title": "Creating Your Account", "content": "1. Go to kanbix.io/signup. 2. Enter email/password. 3. Verify email. 4. Choose plan. 5. Complete onboarding.", "category": "getting_started"},
    {"title": "Inviting Team Members", "content": "Go to Settings > Team Members. Click 'Invite' and enter email. Assign role: Admin, Member, or Viewer.", "category": "team_management"},
    {"title": "Kanban Boards", "content": "Boards contain lists (columns) representing stages like To Do, In Progress, Done. Drag cards to move them.", "category": "features"},
    {"title": "Workflow Automations", "content": "Available on Starter (5) and Pro/Enterprise (unlimited). Consists of a Trigger (e.g. Card moved) and an Action (e.g. Notify Slack).", "category": "automations"},
    {"title": "Subscription Tiers", "content": "Free ($0): 1 user, 3 boards. Starter ($9): 5 automations. Pro ($19): Unlimited everything. Enterprise: Custom pricing.", "category": "billing"},
    {"title": "Slack Integration", "content": "Settings > Integrations > Slack > Connect. Receive notifications, create cards with /kanbix create.", "category": "integrations"},
    {"title": "GitHub Integration", "content": "Link commits/PRs to cards. Auto-move cards when PR is merged. Requires Pro plan.", "category": "integrations"},
    {"title": "Refund Policy", "content": "14-day money-back guarantee. Refund processing must be handled by a human agent. AI cannot process refunds.", "category": "billing"},
    {"title": "Password Reset", "content": "Go to kanbix.io/login > 'Forgot Password' > enter email. Link expires in 1 hour.", "category": "troubleshooting"},
    {"title": "Mobile App Features", "content": "Kanbix mobile app supports iOS and Android. View boards, move cards, get push notifications. Offline mode available on Pro plan.", "category": "features"},
    {"title": "API Access", "content": "REST API available on Pro and Enterprise plans. Rate limit: 100 requests/minute (Pro), 1000/minute (Enterprise). API key in Settings > API.", "category": "features"},
    {"title": "Security & Compliance", "content": "SOC 2 Type II compliant. Data encrypted at rest (AES-256) and in transit (TLS 1.3). GDPR compliant with data export on request.", "category": "security"},
]


async def generate_embedding(text: str) -> list:
    """Generates an embedding vector using Gemini API."""
    attempts = [
        ("v1beta", "gemini-embedding-001"),
        ("v1beta", "text-embedding-004"),
        ("v1", "text-embedding-004"),
        ("v1beta", "embedding-001"),
        ("v1", "embedding-001"),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for version, model in attempts:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:embedContent?key={GEMINI_API_KEY}"
            payload = {
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": 768,
            }
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    values = response.json()["embedding"]["values"][:768]
                    print(f"  Embedding generated ({len(values)} dims) using {model}")
                    return values
            except Exception as e:
                continue

    print("  WARNING: All embedding attempts failed, inserting without embedding")
    return None


async def seed():
    conn = await get_db_conn()
    print("Seeding knowledge base with embeddings...")
    try:
        await conn.execute("DELETE FROM knowledge_base")

        for i, doc in enumerate(SAMPLE_DOCS):
            print(f"[{i+1}/{len(SAMPLE_DOCS)}] {doc['title']}...")

            # Generate embedding from title + content
            embed_text = f"{doc['title']}: {doc['content']}"
            embedding = await generate_embedding(embed_text)

            if embedding:
                vector_str = f"[{','.join(map(str, embedding))}]"
                await conn.execute(
                    "INSERT INTO knowledge_base (title, content, category, embedding) VALUES ($1, $2, $3, $4)",
                    doc["title"], doc["content"], doc["category"], vector_str,
                )
            else:
                await conn.execute(
                    "INSERT INTO knowledge_base (title, content, category) VALUES ($1, $2, $3)",
                    doc["title"], doc["content"], doc["category"],
                )

        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
        embed_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base WHERE embedding IS NOT NULL")
        print(f"\nKnowledge base seeded: {count} docs total, {embed_count} with embeddings.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
