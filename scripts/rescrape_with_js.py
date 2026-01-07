"""
Enhanced Re-Scraper with JavaScript Rendering
==============================================

PURPOSE:
    Re-scrape existing URLs with JavaScript rendering enabled to capture
    all dynamic content (tabs, accordions, fee tables, etc.) that was
    missed by the original scraper.

WHAT IT DOES:
    1. Gets all existing document URLs from database
    2. Re-scrapes each with JS rendering enabled
    3. Updates the document content in database
    4. Deletes old chunks for that document
    5. Re-chunks and generates new embeddings

USAGE:
    python scripts/rescrape_with_js.py [--test] [--limit N] [--category CATEGORY]
    
    --test      : Test mode - scrape only 2 URLs to verify
    --limit N   : Limit to N URLs
    --category  : Only scrape specific category (e.g., 'courses')

Author: Baqar
Date: Jan 2026
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import Firecrawl
import psycopg2
from psycopg2.extras import Json
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
FIRECRAWL_API_KEY_BACKUP = os.getenv('FIRECRAWL_API_KEY_BACKUP')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Track if we've switched to backup key
using_backup_key = False

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'stirling_chat'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

# Scraping settings
DELAY_BETWEEN_REQUESTS = 3  # Seconds between requests
JS_WAIT_TIME = 5000  # Milliseconds to wait for JS to render (5 seconds)
CHUNK_SIZE = 600  # Tokens per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks


def connect_to_database():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Connected to database")
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None


def get_documents_to_rescrape(conn, category=None, limit=None):
    """
    Get list of documents to re-scrape.
    
    Args:
        conn: Database connection
        category: Optional category filter
        limit: Optional limit on number of URLs
        
    Returns:
        List of (id, url, category) tuples
    """
    cursor = conn.cursor()
    
    query = "SELECT id, url, category FROM documents"
    params = []
    
    if category:
        query += " WHERE category = %s"
        params.append(category)
    
    query += " ORDER BY id"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    cursor.execute(query, params)
    documents = cursor.fetchall()
    cursor.close()
    
    return documents


def scrape_with_js(client, url, max_retries=3):
    """
    Scrape URL with JavaScript rendering enabled.
    
    This captures:
    - Dynamically loaded content
    - Tab content (by clicking on tabs)
    - Accordion content
    - Fee tables
    - Any JS-rendered elements
    
    Args:
        client: FireCrawl client
        url: URL to scrape
        max_retries: Number of retry attempts
        
    Returns:
        Scraped result or None
    """
    # Check if this is a course page that has tabs
    is_course_page = '/courses/pg-taught/' in url or '/courses/ug/' in url
    
    for attempt in range(max_retries):
        try:
            # For course pages, click on all tabs to reveal hidden content (like fees)
            # Tab selectors on Stirling website: #tab_1_1, #tab_1_2, #tab_1_3, #tab_1_4, #tab_1_5
            if is_course_page:
                actions = [
                    {"type": "wait", "milliseconds": 2000},  # Wait for page to load
                    {"type": "click", "selector": "#tab_1_2"},  # Entry requirements tab
                    {"type": "wait", "milliseconds": 500},
                    {"type": "click", "selector": "#tab_1_3"},  # Course details tab
                    {"type": "wait", "milliseconds": 500},
                    {"type": "click", "selector": "#tab_1_4"},  # Fees and funding tab (THIS HAS THE FEES!)
                    {"type": "wait", "milliseconds": 1000},  # Extra wait for fee data to load
                    {"type": "click", "selector": "#tab_1_5"},  # After you graduate tab
                    {"type": "wait", "milliseconds": 500},
                    {"type": "scrape"},  # Now scrape with all tabs expanded
                ]
                
                result = client.scrape(
                    url,
                    formats=['markdown'],
                    wait_for=JS_WAIT_TIME,
                    only_main_content=True,
                    remove_base64_images=True,
                    timeout=90000,  # Longer timeout for actions
                    actions=actions,
                )
            else:
                # For non-course pages, just scrape with JS rendering
                result = client.scrape(
                    url,
                    formats=['markdown'],
                    wait_for=JS_WAIT_TIME,
                    only_main_content=True,
                    remove_base64_images=True,
                    timeout=60000,
                )
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # Credit exhaustion - try backup key or stop
            if "402" in error_msg or "credits" in error_msg.lower():
                global using_backup_key
                if not using_backup_key and FIRECRAWL_API_KEY_BACKUP:
                    print(f"\n[WARN] Primary API credits exhausted. Switching to backup key...")
                    using_backup_key = True
                    raise Exception("SWITCH_TO_BACKUP")
                else:
                    print(f"\n[CRITICAL] API Credits Exhausted (no backup available)!")
                    raise Exception("CREDITS_EXHAUSTED")
            
            # Rate limit - wait and retry
            if "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = 30 * (attempt + 1)
                print(f"  [WAIT] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Other errors - retry with backoff
            if attempt < max_retries - 1:
                print(f"  [RETRY] Attempt {attempt + 1} failed: {error_msg[:50]}")
                time.sleep(5)
                continue
            else:
                print(f"  [FAIL] {error_msg[:80]}")
                return None
    
    return None


def update_document(conn, doc_id, url, result):
    """
    Update document content in database.
    
    Args:
        conn: Database connection
        doc_id: Document ID
        url: Document URL
        result: Scraped result from FireCrawl
        
    Returns:
        True if successful, markdown content
    """
    try:
        cursor = conn.cursor()
        
        # Extract content - handle both dict and object responses
        if isinstance(result, dict):
            markdown_content = result.get('markdown', '')
            metadata = result.get('metadata', {})
        else:
            markdown_content = getattr(result, 'markdown', '')
            metadata = getattr(result, 'metadata', {})
        
        # Extract metadata fields
        if isinstance(metadata, dict):
            title = metadata.get('title', '')
            description = metadata.get('description', '')
        else:
            title = getattr(metadata, 'title', '') if metadata else ''
            description = getattr(metadata, 'description', '') if metadata else ''
        
        content_length = len(markdown_content)
        estimated_chunks = max(1, content_length // 2400)
        
        # Update document
        cursor.execute("""
            UPDATE documents SET
                markdown_content = %s,
                title = %s,
                description = %s,
                content_length = %s,
                estimated_chunks = %s,
                updated_at = NOW(),
                metadata = COALESCE(metadata, '{}'::jsonb) || %s
            WHERE id = %s
        """, (
            markdown_content,
            title,
            description,
            content_length,
            estimated_chunks,
            Json({'js_rendered': True, 'rescrape_date': datetime.now().isoformat()}),
            doc_id
        ))
        
        conn.commit()
        cursor.close()
        return True, markdown_content
        
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] Failed to update document: {e}")
        return False, None


def delete_old_chunks(conn, doc_id):
    """Delete existing chunks for a document."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        return deleted
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] Failed to delete chunks: {e}")
        return 0


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target size in tokens (approx 4 chars per token)
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Approximate chars per chunk (4 chars per token)
    char_size = chunk_size * 4
    char_overlap = overlap * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + char_size
        
        # Try to break at paragraph or sentence
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + char_size // 2:
                end = para_break
            else:
                # Look for sentence break
                for punct in ['. ', '! ', '? ']:
                    sent_break = text.rfind(punct, start, end)
                    if sent_break > start + char_size // 2:
                        end = sent_break + 1
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - char_overlap
        if start >= len(text):
            break
    
    return chunks


def generate_embedding(openai_client, text):
    """Generate embedding for text using OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  [ERROR] Embedding failed: {e}")
        return None


def create_chunks_with_embeddings(conn, openai_client, doc_id, url, content):
    """
    Create chunks with embeddings for a document.
    
    Args:
        conn: Database connection
        openai_client: OpenAI client
        doc_id: Document ID
        url: Document URL
        content: Markdown content
        
    Returns:
        Number of chunks created
    """
    chunks = chunk_text(content)
    
    if not chunks:
        return 0
    
    cursor = conn.cursor()
    created = 0
    
    for i, chunk_text_content in enumerate(chunks):
        # Generate embedding
        embedding = generate_embedding(openai_client, chunk_text_content)
        
        if embedding:
            try:
                cursor.execute("""
                    INSERT INTO chunks (document_id, content, chunk_index, embedding)
                    VALUES (%s, %s, %s, %s)
                """, (doc_id, chunk_text_content, i, embedding))
                created += 1
            except Exception as e:
                print(f"  [ERROR] Failed to insert chunk {i}: {e}")
    
    conn.commit()
    cursor.close()
    return created


def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Re-scrape URLs with JS rendering')
    parser.add_argument('--test', action='store_true', help='Test mode (2 URLs only)')
    parser.add_argument('--limit', type=int, help='Limit number of URLs')
    parser.add_argument('--category', type=str, help='Filter by category')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("ENHANCED RE-SCRAPER WITH JAVASCRIPT RENDERING")
    print("=" * 60)
    
    # Validate API keys
    if not FIRECRAWL_API_KEY:
        print("[ERROR] FIRECRAWL_API_KEY not found in .env")
        return
    
    if not OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY not found in .env")
        return
    
    print(f"[OK] API keys found")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    # Initialize clients
    firecrawl_client = Firecrawl(api_key=FIRECRAWL_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("[OK] Clients initialized")
    
    # Get documents to re-scrape
    limit = 2 if args.test else args.limit
    documents = get_documents_to_rescrape(conn, args.category, limit)
    
    print(f"\n[INFO] Documents to re-scrape: {len(documents)}")
    
    if args.test:
        print("[TEST MODE] Only processing 2 URLs")
    
    if not documents:
        print("[INFO] No documents found")
        conn.close()
        return
    
    # Statistics
    stats = {
        'total': len(documents),
        'updated': 0,
        'failed': 0,
        'chunks_created': 0,
        'start_time': time.time()
    }
    
    print("\n" + "-" * 60)
    print("Starting re-scrape with JS rendering...")
    print("-" * 60 + "\n")
    
    # Process each document
    for i, (doc_id, url, category) in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] {url[:70]}...")
        
        try:
            # 1. Scrape with JS rendering
            result = scrape_with_js(firecrawl_client, url)
            
            if not result:
                stats['failed'] += 1
                continue
            
            # 2. Update document and get markdown
            success, markdown = update_document(conn, doc_id, url, result)
            
            if not success or not markdown:
                stats['failed'] += 1
                continue
            
            # 3. Delete old chunks
            deleted = delete_old_chunks(conn, doc_id)
            
            # 4. Create new chunks with embeddings
            created = create_chunks_with_embeddings(conn, openai_client, doc_id, url, markdown)
            
            stats['updated'] += 1
            stats['chunks_created'] += created
            
            print(f"  [OK] Updated: {len(markdown):,} chars, {created} chunks (deleted {deleted} old)")
            
        except Exception as e:
            error_str = str(e)
            if "CREDITS_EXHAUSTED" in error_str:
                print("\n[STOPPED] Credits exhausted. Run again later to continue.")
                break
            elif "SWITCH_TO_BACKUP" in error_str:
                # Switch to backup key and retry this URL
                print("[INFO] Reinitializing client with backup API key...")
                firecrawl_client = Firecrawl(api_key=FIRECRAWL_API_KEY_BACKUP)
                print("[OK] Switched to backup API key. Retrying...")
                # Retry the same URL
                try:
                    result = scrape_with_js(firecrawl_client, url)
                    if result:
                        success, markdown = update_document(conn, doc_id, url, result)
                        if success and markdown:
                            deleted = delete_old_chunks(conn, doc_id)
                            created = create_chunks_with_embeddings(conn, openai_client, doc_id, url, markdown)
                            stats['updated'] += 1
                            stats['chunks_created'] += created
                            print(f"  [OK] Updated: {len(markdown):,} chars, {created} chunks (deleted {deleted} old)")
                        else:
                            stats['failed'] += 1
                    else:
                        stats['failed'] += 1
                except Exception as retry_e:
                    if "CREDITS_EXHAUSTED" in str(retry_e):
                        print("\n[STOPPED] Backup credits also exhausted.")
                        break
                    stats['failed'] += 1
                    print(f"  [ERROR] Retry failed: {retry_e}")
            else:
                stats['failed'] += 1
                print(f"  [ERROR] {e}")
        
        # Delay between requests
        if i < len(documents):
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Summary
    elapsed = time.time() - stats['start_time']
    
    print("\n" + "=" * 60)
    print("RE-SCRAPE COMPLETE")
    print("=" * 60)
    print(f"\nTotal documents: {stats['total']}")
    print(f"Successfully updated: {stats['updated']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total chunks created: {stats['chunks_created']}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    
    if stats['updated'] > 0:
        print(f"Average: {stats['updated']/(elapsed/60):.1f} docs/minute")
    
    print("\n[DONE] Database updated with JS-rendered content")
    
    conn.close()


if __name__ == "__main__":
    main()
