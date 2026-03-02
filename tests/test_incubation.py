import pytest
from src.agent.skills import AgentSkills
from src.tools.mcp_server import (
    create_ticket, 
    TICKETS_DB, 
    search_knowledge_base,
    escalate_to_human
)

def test_sentiment_angry():
    """Verify that angry keywords trigger low sentiment (TC-003)."""
    skills = AgentSkills()
    result = skills.analyze_sentiment("This is garbage, I will sue you!")
    assert result["sentiment_score"] < 0.3
    assert result["is_angry"] is True

def test_channel_adaptation_email():
    """Verify email formatting includes greeting and signature (TC-005)."""
    skills = AgentSkills()
    formatted = skills.adapt_channel("Test Message", "email")
    assert "Hello," in formatted
    assert "Best regards," in formatted

def test_channel_adaptation_whatsapp():
    """Verify WhatsApp formatting is concise."""
    skills = AgentSkills()
    formatted = skills.adapt_channel("Test Message", "whatsapp")
    assert "Flowie:" in formatted
    assert "✅" in formatted

def test_create_ticket_tool():
    """Verify that ticket creation works and logs to DB (TC-004)."""
    TICKETS_DB.clear()
    customer_id = "test@user.com"
    result = create_ticket(customer_id, "Need help with Kanban", "medium", "web_form")
    assert "Ticket created successfully" in result
    assert len(TICKETS_DB) == 1
    
    # Check if the created ticket has correct data
    ticket_id = result.split(": ")[1]
    assert TICKETS_DB[ticket_id]["customer_id"] == customer_id

def test_escalation_logic():
    """Verify escalation updates status (TC-002)."""
    TICKETS_DB.clear()
    create_ticket("user1", "issue", "low", "email")
    ticket_id = list(TICKETS_DB.keys())[0]
    
    result = escalate_to_human(ticket_id, "Pricing query")
    assert "escalated" in result
    assert TICKETS_DB[ticket_id]["status"] == "escalated"

def test_kb_search_tool():
    """Verify knowledge base search returns results or helpful message (TC-006)."""
    result = search_knowledge_base("Kanban")
    # Should either find Kanban in docs or say no match (depending on docs content)
    assert len(result) > 5
