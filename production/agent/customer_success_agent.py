# customer_success_agent.py
import os
import itertools
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT

load_dotenv()

# --- API Key Rotation for Gemini Free Tier (5 req/min per key) ---
# Load all available API keys from .env
_all_api_keys = [v for k, v in os.environ.items() if k.startswith("GEMINI_KEY_")]
# Also include the primary api_key
_primary_key = os.getenv("api_key")
if _primary_key and _primary_key not in _all_api_keys:
    _all_api_keys.insert(0, _primary_key)

if not _all_api_keys:
    print("WARNING: No Gemini API keys found. Real agent calls will fail.")
    _all_api_keys = ["missing_key"]
else:
    print(f"[GEMINI] Loaded {len(_all_api_keys)} API key(s) for rotation (= {len(_all_api_keys) * 5} req/min free tier)")

# Round-robin key iterator
_key_cycle = itertools.cycle(_all_api_keys)
_current_key = next(_key_cycle)

def get_next_api_key() -> str:
    """Rotate to next API key."""
    global _current_key
    _current_key = next(_key_cycle)
    return _current_key

def get_current_api_key() -> str:
    return _current_key

external_client = AsyncOpenAI(
    api_key=_current_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Use gemini-2.0-flash for higher free-tier quota (separate from 2.5-flash)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
model = OpenAIChatCompletionsModel(
    model=GEMINI_MODEL,
    openai_client=external_client
)

from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response
)

# Define the production agent with tools
customer_success_agent = Agent(
    name="Flowie",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    model=model,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response
    ]
)

def get_run_config():
    """Returns the run configuration for the agent."""
    return RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

if __name__ == "__main__":
    print("SaaSFlow Production Agent Loaded. Run via message_processor.py for real tickets.")
