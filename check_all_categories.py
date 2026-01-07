"""Check all document categories and their JS-rendered status"""
import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

cur.execute("""
    SELECT 
        category, 
        COUNT(*) as total,
        SUM(CASE WHEN metadata->>'js_rendered' = 'true' THEN 1 ELSE 0 END) as js_rendered
    FROM documents 
    GROUP BY category 
    ORDER BY total DESC
""")

print("=" * 60)
print("DOCUMENT CATEGORIES IN DATABASE")
print("=" * 60)
print(f"{'Category':<30} {'Total':>8} {'JS Rendered':>12}")
print("-" * 60)

total_docs = 0
total_js = 0
for r in cur.fetchall():
    cat = r[0] or 'uncategorized'
    total = r[1]
    js = r[2] or 0
    total_docs += total
    total_js += js
    status = "✓ ALL" if js == total else f"{js}/{total}"
    print(f"{cat:<30} {total:>8} {status:>12}")

print("-" * 60)
print(f"{'TOTAL':<30} {total_docs:>8} {total_js:>12}")
print("=" * 60)

# Show pages NOT yet JS-rendered
cur.execute("""
    SELECT category, COUNT(*) 
    FROM documents 
    WHERE metadata->>'js_rendered' IS NULL OR metadata->>'js_rendered' != 'true'
    GROUP BY category
    ORDER BY COUNT(*) DESC
""")

results = cur.fetchall()
if results:
    print("\nPages NOT yet re-scraped with JS:")
    for r in results:
        print(f"  {r[0] or 'uncategorized'}: {r[1]} pages")
else:
    print("\n[OK] All pages have been re-scraped with JS!")

conn.close()
