-- RA3G Agent: PostgreSQL schema for hybrid PII storage (Issue #38)
-- Run once on first startup (docker-entrypoint-initdb.d).

CREATE TABLE IF NOT EXISTS pii_records (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(50) DEFAULT 'passage',
    encrypted_data BYTEA NOT NULL,
    encryption_key_id VARCHAR(100) DEFAULT 'default',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    passage_index INTEGER NOT NULL,
    faiss_id INTEGER NOT NULL,
    pii_record_id INTEGER REFERENCES pii_records(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(faiss_id)
);

CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    query_text TEXT,
    redacted_response TEXT,
    governance_decision JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_faiss_id ON documents(faiss_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_session ON query_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at);
