-- Database initialization script for Stirling Chat
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Create a test to ensure pgvector is working
-- This will be replaced by actual tables later
CREATE TABLE IF NOT EXISTS _pgvector_test (
    id SERIAL PRIMARY KEY,
    embedding vector(3)
);

-- Insert test data
INSERT INTO _pgvector_test (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

-- Test vector operations
SELECT * FROM _pgvector_test ORDER BY embedding <-> '[3,3,3]' LIMIT 1;

-- Clean up test table
DROP TABLE _pgvector_test;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension successfully initialized!';
END $$;
