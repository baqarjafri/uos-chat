"""
Text Chunking Script for Stirling Chat MVP
==========================================

PURPOSE:
    Split scraped documents into chunks for RAG system using LangChain
    
FEATURES:
    - Markdown-aware splitting (respects heading boundaries)
    - 800 token chunks with 200 token overlap
    - Heading context tracking (e.g., "BSc Computer Science > Entry Requirements")
    - Intelligent metadata extraction
    - Progress tracking with tqdm
    
USAGE:
    python scripts/process_chunks.py
    
OUTPUT:
    - Chunks inserted into 'chunks' table
    - Summary report with statistics
    
REQUIREMENTS:
    - Database schema updated (run update_chunks_schema.sql first)
    - LangChain installed
    - tiktoken installed
    
Author: Stirling Chat Team
Date: November 18, 2025
"""

import os
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'stirling_chat'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

# Chunking configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 800))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))

# Initialize tiktoken encoder
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

# Initialize LangChain text splitter with markdown-aware separators
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-3.5-turbo",
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=[
        "\n# ",      # H1 headers - highest priority
        "\n## ",     # H2 headers
        "\n### ",    # H3 headers
        "\n#### ",   # H4 headers
        "\n##### ",  # H5 headers
        "\n\n",      # Paragraphs
        "\n",        # Lines
        ". ",        # Sentences
        " ",         # Words
        ""           # Characters
    ]
)


def count_tokens(text):
    """
    Count tokens using tiktoken encoder
    
    Args:
        text (str): Text to count tokens for
        
    Returns:
        int: Number of tokens
    """
    return len(encoding.encode(text))


def extract_heading_context(chunk_text):
    """
    Extract heading hierarchy from chunk text
    
    Looks for markdown headers (# ## ###) and builds a hierarchy string.
    
    Args:
        chunk_text (str): The chunk text to analyze
        
    Returns:
        str: Heading hierarchy like "BSc Computer Science > Entry Requirements > International Students"
             or None if no headers found
    
    Example:
        Input: "## Entry Requirements\n### International Students\nYou need..."
        Output: "Entry Requirements > International Students"
    """
    lines = chunk_text.split('\n')
    headers = []
    
    for line in lines[:10]:  # Check first 10 lines for headers
        line = line.strip()
        if line.startswith('#'):
            # Extract header level and text
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                
                # Remove any trailing markdown (like links, bold, etc.)
                header_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', header_text)  # Remove links
                header_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', header_text)  # Remove bold
                header_text = re.sub(r'\*([^\*]+)\*', r'\1', header_text)  # Remove italic
                
                headers.append((level, header_text))
    
    if not headers:
        return None
    
    # Build hierarchy (keep only increasing or same level headers)
    hierarchy = []
    last_level = 0
    
    for level, text in headers:
        if level <= last_level and hierarchy:
            # Remove headers of same or lower level
            hierarchy = [(l, h) for l, h in hierarchy if l < level]
        hierarchy.append((level, text))
        last_level = level
    
    # Return just the header texts joined with >
    return " > ".join([text for level, text in hierarchy]) if hierarchy else None


def extract_metadata(chunk_text, category):
    """
    Extract intelligent metadata from chunk for better filtering
    
    Analyzes chunk content to determine:
    - Section type (entry_requirements, fees, deadlines, etc.)
    - Program level (undergraduate, postgraduate)
    - Audience (international, domestic)
    - Content flags (has dates, fees, requirements)
    
    Args:
        chunk_text (str): The chunk text to analyze
        category (str): Document category (courses, study, etc.)
        
    Returns:
        dict: Metadata dictionary with extracted information
    """
    text_lower = chunk_text.lower()
    
    metadata = {
        "section_type": None,
        "program_level": None,
        "audience": None,
        "has_dates": False,
        "has_fees": False,
        "has_requirements": False,
        "category": category
    }
    
    # Section type detection
    if any(word in text_lower for word in ['entry requirement', 'admission requirement', 'qualification', 'entry criteria']):
        metadata['section_type'] = 'entry_requirements'
    elif any(word in text_lower for word in ['fee', 'cost', 'tuition', 'funding', 'scholarship', 'bursary']):
        metadata['section_type'] = 'fees_funding'
    elif any(word in text_lower for word in ['deadline', 'key date', 'semester date', 'term date', 'intake', 'start date']):
        metadata['section_type'] = 'deadlines'
    elif any(word in text_lower for word in ['course structure', 'module', 'curriculum', 'year 1', 'year 2', 'syllabus']):
        metadata['section_type'] = 'course_structure'
    elif any(word in text_lower for word in ['accommodation', 'housing', 'residence', 'halls']):
        metadata['section_type'] = 'accommodation'
    elif any(word in text_lower for word in ['how to apply', 'application process', 'ucas', 'apply online']):
        metadata['section_type'] = 'application_process'
    elif any(word in text_lower for word in ['career', 'employment', 'graduate outcome', 'job prospect']):
        metadata['section_type'] = 'careers'
    elif any(word in text_lower for word in ['campus', 'facilities', 'library', 'sport']):
        metadata['section_type'] = 'campus_facilities'
    
    # Program level detection
    if any(word in text_lower for word in ['undergraduate', 'bachelor', 'bsc', 'ba', 'beng', 'llb']):
        metadata['program_level'] = 'undergraduate'
    elif any(word in text_lower for word in ['postgraduate', 'master', 'msc', 'ma', 'mba', 'mres', 'phd', 'doctorate']):
        metadata['program_level'] = 'postgraduate'
    
    # Audience detection
    if any(word in text_lower for word in ['international student', 'overseas student', 'non-uk', 'non-eu']):
        metadata['audience'] = 'international'
    elif any(word in text_lower for word in ['uk student', 'home student', 'scottish student', 'eu student']):
        metadata['audience'] = 'domestic'
    
    # Content flags
    months = ['january', 'february', 'march', 'april', 'may', 'june', 
              'july', 'august', 'september', 'october', 'november', 'december']
    metadata['has_dates'] = any(month in text_lower for month in months) or 'deadline' in text_lower
    
    metadata['has_fees'] = '£' in chunk_text or any(word in text_lower for word in ['fee', 'cost', 'tuition', 'price'])
    
    metadata['has_requirements'] = any(word in text_lower for word in [
        'require', 'qualification', 'ielts', 'toefl', 'a-level', 'higher', 
        'gcse', 'international baccalaureate', 'ib diploma'
    ])
    
    return metadata


def process_chunks():
    """
    Main chunking process
    
    Workflow:
    1. Connect to database
    2. Fetch all documents with markdown content
    3. For each document:
       - Split into chunks using LangChain
       - Extract heading context
       - Extract metadata
       - Count tokens
    4. Batch insert all chunks
    5. Generate summary statistics
    """
    
    print("\n" + "="*70)
    print("MARKDOWN-AWARE CHUNKING - LangChain + tiktoken")
    print("="*70 + "\n")
    
    print(f"⚙️  Configuration:")
    print(f"   Chunk size: {CHUNK_SIZE} tokens")
    print(f"   Overlap: {CHUNK_OVERLAP} tokens")
    print(f"   Strategy: Markdown-aware (respects headers)\n")
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"✅ Connected to database: {DB_CONFIG['database']}\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Clear existing chunks (optional - comment out if you want to keep old chunks)
    print("🗑️  Clearing existing chunks...")
    cursor.execute("DELETE FROM chunks;")
    conn.commit()
    print("✅ Existing chunks cleared\n")
    
    # Get all documents with markdown content
    cursor.execute("""
        SELECT id, url, title, category, markdown_content
        FROM documents
        WHERE markdown_content IS NOT NULL 
        AND markdown_content != ''
        ORDER BY category, title;
    """)
    
    documents = cursor.fetchall()
    total_docs = len(documents)
    
    if total_docs == 0:
        print("❌ No documents found with markdown content!")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    print(f"📄 Found {total_docs:,} documents to process\n")
    print("🔄 Processing documents...\n")
    
    # Process each document
    all_chunks = []
    total_chunks = 0
    skipped_docs = 0
    
    for doc_id, url, title, category, markdown_content in tqdm(documents, desc="Chunking", unit="doc"):
        
        # Skip if markdown is empty or too short
        if not markdown_content or len(markdown_content.strip()) < 100:
            skipped_docs += 1
            continue
        
        try:
            # Split using LangChain (markdown-aware)
            langchain_chunks = text_splitter.create_documents(
                texts=[markdown_content],
                metadatas=[{
                    "url": url,
                    "title": title,
                    "category": category
                }]
            )
            
            # Process each chunk
            for idx, lc_chunk in enumerate(langchain_chunks):
                chunk_text = lc_chunk.page_content
                
                # Skip empty chunks
                if not chunk_text.strip():
                    continue
                
                # Extract heading context
                heading_context = extract_heading_context(chunk_text)
                
                # Extract metadata
                chunk_metadata = extract_metadata(chunk_text, category)
                
                # Count tokens
                token_count = count_tokens(chunk_text)
                
                # Prepare for database insert
                all_chunks.append((
                    doc_id,                          # document_id
                    idx,                             # chunk_index
                    len(langchain_chunks),           # total_chunks
                    chunk_text,                      # content
                    heading_context,                 # heading_context
                    token_count,                     # token_count
                    json.dumps(chunk_metadata)       # metadata (JSONB)
                ))
                
                total_chunks += 1
        
        except Exception as e:
            print(f"\n⚠️  Error processing document {doc_id} ({title}): {e}")
            skipped_docs += 1
            continue
    
    # Batch insert into database
    print(f"\n\n💾 Inserting {total_chunks:,} chunks into database...")
    
    try:
        execute_batch(cursor, """
            INSERT INTO chunks 
                (document_id, chunk_index, total_chunks, content, heading_context, token_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, all_chunks, page_size=100)
        
        conn.commit()
        print(f"✅ Successfully inserted {total_chunks:,} chunks\n")
    
    except Exception as e:
        print(f"❌ Error inserting chunks: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        sys.exit(1)
    
    # Generate summary statistics
    print("="*70)
    print("CHUNKING SUMMARY")
    print("="*70 + "\n")
    
    cursor.execute("""
        SELECT 
            d.category,
            COUNT(c.id) as chunk_count,
            ROUND(AVG(c.token_count)) as avg_tokens,
            MIN(c.token_count) as min_tokens,
            MAX(c.token_count) as max_tokens
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        GROUP BY d.category
        ORDER BY chunk_count DESC;
    """)
    
    print(f"{'Category':<20} | {'Chunks':>6} | {'Avg':>4} | {'Min':>4} | {'Max':>4}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        category, count, avg, min_tok, max_tok = row
        print(f"{category:<20} | {count:>6} | {avg:>4.0f} | {min_tok:>4} | {max_tok:>4}")
    
    # Overall statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_chunks,
            ROUND(AVG(token_count)) as avg_tokens,
            COUNT(DISTINCT document_id) as docs_with_chunks,
            COUNT(*) FILTER (WHERE heading_context IS NOT NULL) as chunks_with_headings
        FROM chunks;
    """)
    
    stats = cursor.fetchone()
    total_chunks_db, avg_tokens, docs_with_chunks, chunks_with_headings = stats
    
    print("\n" + "="*70)
    print(f"✅ Total chunks created: {total_chunks_db:,}")
    print(f"📊 Average tokens per chunk: {avg_tokens:.0f}")
    print(f"📄 Documents processed: {docs_with_chunks:,} / {total_docs:,}")
    print(f"🏷️  Chunks with headings: {chunks_with_headings:,} ({chunks_with_headings/total_chunks_db*100:.1f}%)")
    
    if skipped_docs > 0:
        print(f"⚠️  Skipped documents: {skipped_docs}")
    
    print(f"\n📈 Average chunks per document: {total_chunks_db/docs_with_chunks:.1f}")
    print(f"💾 Database: chunks table updated")
    print(f"⏰ Completed at: {datetime.now().strftime('%I:%M:%S %p')}\n")
    
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Generate embeddings: python scripts/generate_embeddings.py")
    print("2. Test vector search: python scripts/test_search.py")
    print("3. Build RAG system: python scripts/query_rag.py\n")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        process_chunks()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
