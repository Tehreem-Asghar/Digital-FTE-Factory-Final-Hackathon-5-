import time
from src.agent.loader import ContextLoader
from src.agent.skills import AgentSkills
from src.tools.mcp_server import (
    create_ticket, 
    search_knowledge_base, 
    send_response, 
    escalate_to_human,
    get_customer_history
)

def run_simulation():
    """Simulates the Digital FTE processing sample tickets."""
    loader = ContextLoader()
    skills = AgentSkills()
    tickets = loader.load_tickets()
    
    print("🚀 Starting SaaSFlow Digital FTE Simulation...\n")
    
    for ticket in tickets:
        print(f"--- Processing Ticket: {ticket['id']} ({ticket['channel']}) ---")
        
        # 1. ANALYZE SENTIMENT
        sentiment = skills.analyze_sentiment(ticket['content'])
        print(f"   [Skill] Sentiment: {sentiment['sentiment_score']} (Is Angry: {sentiment['is_angry']})")
        
        # 2. LOG INTERACTION (Create Ticket)
        # Using Email as customer_id as recommended in Exercise 1.3
        customer_id = ticket.get('customer_email') or ticket.get('customer_phone')
        creation_msg = create_ticket(customer_id, ticket['content'], "medium", ticket['channel'])
        ticket_id = creation_msg.split(": ")[1]
        print(f"   [Tool] {creation_msg}")
        
        # 3. GET HISTORY
        history = get_customer_history(customer_id)
        # In prototype, we just log that we retrieved it
        
        # 4. DECIDE ACTION
        if sentiment['is_angry']:
            # IMMEDIATE ESCALATION for low sentiment
            result = escalate_to_human(ticket_id, "Negative sentiment detected.")
            print(f"   [Action] 🔥 {result}")
        elif "refund" in ticket['content'].lower() or "price" in ticket['content'].lower():
            # HARD CONSTRAINT: ESCALATE PRICING/REFUNDS
            result = escalate_to_human(ticket_id, "Hard constraint: Pricing/Refund query.")
            print(f"   [Action] 💰 {result}")
        else:
            # ROUTINE QUERY: SEARCH DOCS
            print(f"   [Action] Searching docs for: '{ticket['content'][:30]}...'")
            kb_result = search_knowledge_base(ticket['content'])
            
            # 5. GENERATE & SEND RESPONSE
            response_text = f"Based on our docs: {kb_result}"
            delivery_msg = send_response(ticket_id, response_text, ticket['channel'])
            print(f"   [Action] ✉️ {delivery_msg}")
            
        print("-" * 50)
        time.sleep(1) # Simulate processing time

if __name__ == "__main__":
    run_simulation()
