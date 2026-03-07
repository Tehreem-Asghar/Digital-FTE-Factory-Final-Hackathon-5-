-- 002_pending_ingestion.sql
-- Fail-safe ingestion table for Kafka downtime resilience (Stage 3)

CREATE TABLE IF NOT EXISTS pending_ingestion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255) NOT NULL DEFAULT 'fte.tickets.incoming',
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'published', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_pending_ingestion_status ON pending_ingestion(status);
CREATE INDEX IF NOT EXISTS idx_pending_ingestion_created ON pending_ingestion(created_at);
