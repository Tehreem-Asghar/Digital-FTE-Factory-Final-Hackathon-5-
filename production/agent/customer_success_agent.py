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

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Use gemini-2.0-flash (found to be working on this endpoint)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def _make_client(api_key: str) -> AsyncOpenAI:
    """Create a new AsyncOpenAI client with max_retries=0 to prevent SDK from wasting keys."""
    # Mask key for logging
    masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"[DEBUG] Creating new Gemini client with key: {masked_key}")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=GEMINI_BASE_URL,
        max_retries=0,  # We handle retries ourselves with key rotation
    )

def _make_model(client: AsyncOpenAI) -> OpenAIChatCompletionsModel:
    return OpenAIChatCompletionsModel(model=GEMINI_MODEL, openai_client=client)

external_client = _make_client(_current_key)
model = _make_model(external_client)

def rotate_client():
    """Rotate to next API key and rebuild client+model so the agent uses the new key."""
    global external_client, model
    new_key = get_next_api_key()
    external_client = _make_client(new_key)
    model = _make_model(external_client)
    # Update the agent's internal model as well
    customer_success_agent.model = model
    return new_key

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
    """Returns the run configuration for the agent, always using the current (possibly rotated) client."""
    return RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

if __name__ == "__main__":
    print("SaaSFlow Production Agent Loaded. Run via message_processor.py for real tickets.")
