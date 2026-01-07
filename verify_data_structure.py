"""Verify the data structure consistency of the re-scraper"""
import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

print("=" * 60)
print("DATABASE SCHEMA VERIFICATION")
print("=" * 60)

# Check documents table structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'documents' 
    ORDER BY ordinal_position
""")
print("\nDOCUMENTS TABLE:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check chunks table structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'chunks' 
    ORDER BY ordinal_position
""")
print("\nCHUNKS TABLE:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n" + "=" * 60)
print("DATA CONSISTENCY CHECK")
print("=" * 60)

# Compare an old document vs newly updated document
cur.execute("""
    SELECT d.id, d.url, d.title, d.content_length, d.estimated_chunks,
           COUNT(c.id) as actual_chunks,
           d.metadata->>'js_rendered' as js_rendered
    FROM documents d
    LEFT JOIN chunks c ON d.id = c.document_id
    WHERE d.category = 'courses'
    GROUP BY d.id
    ORDER BY d.metadata->>'js_rendered' DESC NULLS LAST, d.id
    LIMIT 4
""")
print("\nSample documents (JS-rendered first, then old):")
for r in cur.fetchall():
    print(f"\n  ID: {r[0]}")
    print(f"  URL: {r[1][:60]}...")
    print(f"  Title: {r[2][:50] if r[2] else 'N/A'}...")
    print(f"  Content length: {r[3]}")
    print(f"  Estimated chunks: {r[4]}")
    print(f"  Actual chunks: {r[5]}")
    print(f"  JS Rendered: {r[6]}")

# Check embedding dimensions are consistent (vector type)
cur.execute("""
    SELECT 
        vector_dims(embedding) as embedding_dim,
        COUNT(*) as count
    FROM chunks
    WHERE embedding IS NOT NULL
    GROUP BY vector_dims(embedding)
""")
print("\n\nEMBEDDING DIMENSIONS:")
for r in cur.fetchall():
    print(f"  Dimension {r[0]}: {r[1]} chunks")

print("\n[OK] Data structure verification complete")
conn.close()
