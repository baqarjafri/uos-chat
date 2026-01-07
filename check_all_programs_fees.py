import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/stirling_chat')
cur = conn.cursor()

# Count total program pages in database
print("=" * 60)
print("TOTAL PROGRAM PAGES IN DATABASE")
print("=" * 60)

cur.execute("""
    SELECT COUNT(DISTINCT url) 
    FROM documents 
    WHERE url LIKE '%/courses/pg-taught/%' OR url LIKE '%/courses/ug/%'
""")
total_programs = cur.fetchone()[0]
print(f"\nTotal program pages: {total_programs}")

# Count programs WITH fee amounts (£ symbol)
print("\n" + "=" * 60)
print("PROGRAMS WITH ACTUAL £ FEE AMOUNTS")
print("=" * 60)

cur.execute("""
    SELECT DISTINCT d.url
    FROM documents d
    JOIN chunks c ON d.id = c.document_id
    WHERE (d.url LIKE '%/courses/pg-taught/%' OR d.url LIKE '%/courses/ug/%')
    AND c.content LIKE '%£%'
    AND (c.content ILIKE '%fee%' OR c.content ILIKE '%tuition%')
""")
programs_with_fees = cur.fetchall()
print(f"\nPrograms with £ amounts: {len(programs_with_fees)}")

# Show some examples
print("\nExamples of programs WITH fee data:")
for url in programs_with_fees[:10]:
    print(f"  - {url[0]}")

# Count programs WITHOUT fee amounts
print("\n" + "=" * 60)
print("PROGRAMS WITHOUT £ FEE AMOUNTS")
print("=" * 60)

cur.execute("""
    SELECT DISTINCT d.url
    FROM documents d
    WHERE (d.url LIKE '%/courses/pg-taught/%' OR d.url LIKE '%/courses/ug/%')
    AND d.url NOT IN (
        SELECT DISTINCT d2.url
        FROM documents d2
        JOIN chunks c ON d2.id = c.document_id
        WHERE c.content LIKE '%£%'
        AND (c.content ILIKE '%fee%' OR c.content ILIKE '%tuition%')
    )
""")
programs_without_fees = cur.fetchall()
print(f"\nPrograms WITHOUT £ amounts: {len(programs_without_fees)}")

print("\nExamples of programs MISSING fee data:")
for url in programs_without_fees[:15]:
    print(f"  - {url[0]}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\nTotal programs: {total_programs}")
print(f"With fee data: {len(programs_with_fees)} ({len(programs_with_fees)*100//total_programs}%)")
print(f"Missing fee data: {len(programs_without_fees)} ({len(programs_without_fees)*100//total_programs}%)")

conn.close()
