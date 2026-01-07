import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

# Check CPD course that we know has fees
cur.execute("""
    SELECT c.content 
    FROM chunks c 
    JOIN documents d ON c.document_id = d.id 
    WHERE d.url = 'https://www.stir.ac.uk/courses/cpd-short-courses/adult-support-and-protection' 
    AND c.content LIKE '%Fee%' 
    LIMIT 1
""")
r = cur.fetchone()
print("CPD Course with fees:")
print(r[0] if r else 'No result')

print("\n" + "=" * 60)

# Check if any MSc course has actual tuition fee amounts
cur.execute("""
    SELECT d.url, c.content 
    FROM chunks c 
    JOIN documents d ON c.document_id = d.id 
    WHERE d.url LIKE '%/courses/pg-taught/%'
    AND c.content ~ '£[0-9]{2},[0-9]{3}'
    LIMIT 5
""")
rows = cur.fetchall()
print(f"\nMSc courses with £XX,XXX amounts: {len(rows)}")
for url, content in rows:
    print(f"\nURL: {url}")
    print(f"Content preview: {content[:300]}...")

conn.close()
