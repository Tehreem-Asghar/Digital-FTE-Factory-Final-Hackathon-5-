-- Migration 003: Resolution Learnings table for "Learn from Resolved Tickets"
-- Stores extracted patterns from resolved tickets to improve agent responses over time.

CREATE TABLE IF NOT EXISTS resolution_learnings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id),
    issue_category VARCHAR(100),
    issue_summary TEXT NOT NULL,
    resolution_summary TEXT NOT NULL,
    source_channel VARCHAR(50),
    resolution_time_hours DECIMAL(10,2),
    was_escalated BOOLEAN DEFAULT FALSE,
    keywords TEXT[],
    embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resolution_learnings_category ON resolution_learnings(issue_category);
CREATE INDEX IF NOT EXISTS idx_resolution_learnings_embedding ON resolution_learnings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
