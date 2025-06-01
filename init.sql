-- Initialize database for legal snippets
CREATE EXTENSION IF NOT EXISTS vector;

-- Legal snippets table with vector embeddings
CREATE TABLE IF NOT EXISTS legal_snippets (
    id SERIAL PRIMARY KEY,
    citation TEXT NOT NULL,
    key_language TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    context TEXT DEFAULT '',
    case_type TEXT DEFAULT 'civil',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    citation_embedding vector(384),
    key_language_embedding vector(384),
    combined_embedding vector(384)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_legal_snippets_tags 
ON legal_snippets USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_legal_snippets_case_type 
ON legal_snippets(case_type);

-- Vector similarity indexes (will be created after some data is inserted)
-- CREATE INDEX IF NOT EXISTS idx_legal_snippets_combined_embedding 
-- ON legal_snippets USING ivfflat (combined_embedding vector_cosine_ops)
-- WITH (lists = 100);