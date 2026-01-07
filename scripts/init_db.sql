-- Initialize pgvector extension for PostgreSQL
-- This script runs automatically when the Docker container starts

CREATE EXTENSION IF NOT EXISTS vector;
