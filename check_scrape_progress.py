import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

# Check progress by category
cur.execute("""
    SELECT 
        category,
        COUNT(*) as total,
        SUM(CASE WHEN metadata->>'js_rendered' = 'true' THEN 1 ELSE 0 END) as js_done
    FROM documents 
    WHERE category IN ('courses', 'scholarships', 'international')
    GROUP BY category
    ORDER BY category
""")

print(f"Re-scrape progress by category:")
for r in cur.fetchall():
    cat, total, done = r[0], r[1], r[2] or 0
    pct = (done / total * 100) if total > 0 else 0
    status = "DONE" if done == total else f"{pct:.0f}%"
    print(f"  {cat}: {done}/{total} ({status})")

# Check if MSc AI has been updated
cur.execute("""
    SELECT content FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE d.url = 'https://www.stir.ac.uk/courses/pg-taught/artificial-intelligence'
    AND c.content LIKE '%24,300%'
    LIMIT 1
""")
ai_fee = cur.fetchone()
if ai_fee:
    print(f"\n[OK] MSc AI fee data (£24,300) is now in database!")
else:
    print(f"\n[PENDING] MSc AI fee data not yet updated")

conn.close()
