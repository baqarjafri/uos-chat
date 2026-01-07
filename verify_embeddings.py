"""Verify embeddings are in the database"""
import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

# Count chunks with embeddings
cur.execute('SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL')
print(f"Chunks with embeddings: {cur.fetchone()[0]}")

# Check MSc AI fee chunk
cur.execute("""
    SELECT c.content 
    FROM chunks c 
    JOIN documents d ON c.document_id = d.id 
    WHERE d.url LIKE '%artificial-intelligence%' 
    AND c.content LIKE '%24,300%' 
    LIMIT 1
""")
r = cur.fetchone()
print(f"\nMSc AI fee chunk found: {bool(r)}")
if r:
    print(f"\n--- Fee Chunk Content (first 800 chars) ---")
    print(r[0][:800])

# Show embedding sample
cur.execute("""
    SELECT c.id, c.content, embedding[1:5] as sample_embedding
    FROM chunks c 
    JOIN documents d ON c.document_id = d.id 
    WHERE d.url LIKE '%artificial-intelligence%' 
    AND c.content LIKE '%24,300%' 
    LIMIT 1
""")
r = cur.fetchone()
if r:
    print(f"\n--- Embedding Sample (first 5 dimensions) ---")
    print(f"Chunk ID: {r[0]}")
    print(f"Embedding: {r[2]}")

conn.close()
