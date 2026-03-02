import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from src.agent.loader import ContextLoader
from src.agent.skills import AgentSkills

# Initialize MCP Server
mcp = FastMCP("saasflow-fte")

# In-memory database for prototype
TICKETS_DB: Dict[str, Dict[str, Any]] = {}
context_loader = ContextLoader()
skills = AgentSkills()

@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search product documentation for relevant information."""
    docs = context_loader.load_markdown("product-docs.md")
    # Simple keyword search for prototype
    relevant_lines = []
    for line in docs.split("\n"):
        if query.lower() in line.lower() and len(line.strip()) > 5:
            relevant_lines.append(line.strip())
    
    if not relevant_lines:
        return "No direct match found. Please check manual for: " + query
    return "\n".join(relevant_lines[:5])

@mcp.tool()
def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> str:
    """Create a support ticket in the system with channel tracking."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    TICKETS_DB[ticket_id] = ticket
    return f"Ticket created successfully: {ticket_id}"

@mcp.tool()
def get_customer_history(customer_id: str) -> str:
    """Get customer's interaction history across ALL channels."""
    history = [t for t in TICKETS_DB.values() if t["customer_id"] == customer_id]
    if not history:
        return f"No history found for customer: {customer_id}"
    return json.dumps(history, indent=2)

@mcp.tool()
def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Escalate conversation to human support."""
    if ticket_id in TICKETS_DB:
        TICKETS_DB[ticket_id]["status"] = "escalated"
        TICKETS_DB[ticket_id]["escalation_reason"] = reason
        return f"Ticket {ticket_id} has been escalated to a human specialist. Reason: {reason}"
    return f"Ticket {ticket_id} not found."

@mcp.tool()
def send_response(ticket_id: str, message: str, channel: str) -> str:
    """Send response via the appropriate channel with formatting."""
    formatted_msg = skills.adapt_channel(message, channel)
    if ticket_id in TICKETS_DB:
        TICKETS_DB[ticket_id]["messages"].append({
            "role": "agent",
            "content": formatted_msg,
            "timestamp": datetime.now().isoformat()
        })
    return f"Message delivered via {channel}: {formatted_msg}"

if __name__ == "__main__":
    mcp.run()
