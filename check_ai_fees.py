import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

# First, check table structure
print("=" * 60)
print("CHECKING DATABASE STRUCTURE")
print("=" * 60)

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'chunks'")
columns = [r[0] for r in cur.fetchall()]
print(f"Chunks table columns: {columns}")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'documents'")
doc_columns = [r[0] for r in cur.fetchall()]
print(f"Documents table columns: {doc_columns}")

# Search for MSc AI fee information
print("\n" + "=" * 60)
print("SEARCHING FOR MSc ARTIFICIAL INTELLIGENCE FEE DATA")
print("=" * 60)

# Query with join to get URL from documents table
cur.execute("""
    SELECT c.content, d.url 
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE (c.content ILIKE '%artificial intelligence%' OR c.content ILIKE '%msc ai%')
    AND (c.content ILIKE '%fee%' OR c.content ILIKE '%tuition%' OR c.content ILIKE '%£%')
    LIMIT 10
""")
rows = cur.fetchall()

print(f"\nFound {len(rows)} chunks with AI + fee keywords:\n")
for i, row in enumerate(rows, 1):
    print(f"--- Result {i} ---")
    print(f"URL: {row[1]}")
    print(f"Content: {row[0][:600]}...")
    print()

# Query 2: Search for international fees generally
print("=" * 60)
print("SEARCHING FOR INTERNATIONAL STUDENT FEES")
print("=" * 60)

cur.execute("""
    SELECT c.content, d.url 
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.content ILIKE '%international%' 
    AND (c.content ILIKE '%fee%' OR c.content ILIKE '%£%')
    AND c.content ILIKE '%postgraduate%'
    LIMIT 5
""")
rows = cur.fetchall()

print(f"\nFound {len(rows)} chunks with international + postgraduate + fees:\n")
for i, row in enumerate(rows, 1):
    print(f"--- Result {i} ---")
    print(f"URL: {row[1]}")
    print(f"Content: {row[0][:600]}...")
    print()

# Query 3: Check what URLs we have for AI program
print("=" * 60)
print("CHECKING AI PROGRAM URLS IN DATABASE")
print("=" * 60)

cur.execute("""
    SELECT DISTINCT d.url 
    FROM documents d
    WHERE d.url ILIKE '%artificial-intelligence%'
    LIMIT 10
""")
rows = cur.fetchall()

print(f"\nFound {len(rows)} URLs related to AI program:\n")
for row in rows:
    print(f"  - {row[0]}")

conn.close()
