"""
FireCrawl Web Scraper - Stirling Chat MVP
==========================================

PURPOSE:
    Scrape all 1,206 URLs from Stirling University website using FireCrawl API.
    Save content directly to PostgreSQL database (no intermediate files).

WHAT YOU'LL LEARN:
    - Reading files and directories
    - Database connections and operations
    - API integration with error handling
    - Progress tracking and logging
    - Resume capability after interruptions
    - Real-world production patterns

WORKFLOW:
    1. Connect to database
    2. Read URL files from data/urls/
    3. Check what's already scraped
    4. Scrape remaining URLs
    5. Save to database after each URL
    6. Handle errors gracefully
    7. Show progress and summary

Author: Baqar
Date: Nov 13, 2025
"""

# ============================================
# IMPORTS - External libraries we need
# ============================================

# Standard library (built into Python)
import os                    # Operating system operations (file paths, environment)
import json                  # Working with JSON data
import time                  # Time operations (delays, timestamps)
from datetime import datetime  # Date and time handling
from pathlib import Path     # Modern file path handling

# Third-party libraries (installed via pip)
from dotenv import load_dotenv  # Load environment variables from .env file
from firecrawl import Firecrawl  # FireCrawl SDK for web scraping
import psycopg2                  # PostgreSQL database adapter
from psycopg2.extras import Json # JSON handling for PostgreSQL


# ============================================
# CONFIGURATION - Load settings
# ============================================

# Load environment variables from .env file
# This keeps sensitive data (API keys, passwords) out of code
load_dotenv()

# Get API key from environment
# os.getenv() reads from .env file
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')

# Database connection details
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'stirling_chat'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

# Scraping settings
URLS_DIRECTORY = Path('data/urls')  # Where URL files are stored
DELAY_BETWEEN_REQUESTS = 3          # Seconds to wait between requests (avoid rate limits!)
MAX_RETRIES = 3                     # How many times to retry on error


# ============================================
# HELPER FUNCTIONS - Reusable code blocks
# ============================================

def connect_to_database():
    """
    Connect to PostgreSQL database.
    
    WHAT THIS TEACHES:
    - Database connections
    - Error handling with try/except
    - Returning values from functions
    
    Returns:
        connection object if successful, None if failed
    """
    
    try:
        # psycopg2.connect() creates a connection to PostgreSQL
        # **DB_CONFIG unpacks the dictionary as keyword arguments
        conn = psycopg2.connect(**DB_CONFIG)
        
        print("[SUCCESS] Connected to database")
        return conn
        
    except Exception as e:
        # If connection fails, print error and return None
        print(f"[ERROR] Database connection failed: {e}")
        print("[HELP] Make sure PostgreSQL is running: docker-compose up -d")
        return None


def get_scraped_urls(conn):
    """
    Get list of URLs already scraped from database.
    
    WHAT THIS TEACHES:
    - SQL SELECT queries
    - Cursor operations
    - List comprehension
    - Sets for fast lookup
    
    Args:
        conn: Database connection object
        
    Returns:
        set: Set of URLs already in database
    """
    
    try:
        # Create cursor - used to execute SQL commands
        cursor = conn.cursor()
        
        # SQL query to get all URLs
        # We only need the URL column, not all data
        query = "SELECT url FROM documents;"
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch all results
        # fetchall() returns list of tuples: [('url1',), ('url2',), ...]
        rows = cursor.fetchall()
        
        # Extract just the URLs using list comprehension
        # row[0] gets the first (and only) item from each tuple
        # set() converts to set for fast lookup (O(1) instead of O(n))
        urls = set(row[0] for row in rows)
        
        cursor.close()
        return urls
        
    except Exception as e:
        print(f"[ERROR] Failed to get scraped URLs: {e}")
        return set()  # Return empty set on error


def read_url_files():
    """
    Read all URL files from data/urls/ directory.
    
    WHAT THIS TEACHES:
    - File system operations
    - Path handling with pathlib
    - Reading text files
    - Organizing data by category
    - Dictionary data structures
    
    Returns:
        dict: Dictionary mapping category to list of URLs
              Example: {'courses': ['url1', 'url2'], 'about': ['url3']}
    """
    
    # Dictionary to store URLs by category
    # Key = category name (e.g., 'courses')
    # Value = list of URLs
    url_data = {}
    
    # Check if directory exists
    if not URLS_DIRECTORY.exists():
        print(f"[ERROR] Directory not found: {URLS_DIRECTORY}")
        return url_data
    
    # Find all .txt files in the directory
    # glob('*.txt') returns all files ending with .txt
    txt_files = list(URLS_DIRECTORY.glob('*.txt'))
    
    print(f"\n[STEP] Reading URL files from {URLS_DIRECTORY}")
    print(f"Found {len(txt_files)} URL files\n")
    
    # Process each file
    for file_path in txt_files:
        
        # Get category name from filename
        # file_path.stem gets filename without extension
        # Example: 'courses.txt' -> 'courses'
        category = file_path.stem
        
        # Skip the SUMMARY file (it's documentation, not URLs)
        if category.upper() == 'SUMMARY':
            continue
        
        try:
            # Open and read the file
            # 'r' = read mode, encoding='utf-8' handles special characters
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read all lines
                lines = f.readlines()
            
            # Process lines to extract URLs
            urls = []
            for line in lines:
                # strip() removes whitespace (spaces, newlines, tabs)
                line = line.strip()
                
                # Skip empty lines and comments (lines starting with #)
                if not line or line.startswith('#'):
                    continue
                
                # Add URL to list
                urls.append(line)
            
            # Store in dictionary
            url_data[category] = urls
            
            print(f"  - {category}: {len(urls)} URLs")
            
        except Exception as e:
            print(f"[ERROR] Failed to read {file_path}: {e}")
    
    return url_data


def scrape_url_with_retry(client, url, max_retries=MAX_RETRIES):
    """
    Scrape a URL with retry logic and error handling.
    
    WHAT THIS TEACHES:
    - Retry patterns for reliability
    - Exception handling
    - API integration
    - Error classification
    - Exponential backoff
    
    Args:
        client: FireCrawl client object
        url: URL to scrape
        max_retries: Maximum number of retry attempts
        
    Returns:
        dict: Scraped data if successful, None if failed
    """
    
    # Try scraping up to max_retries times
    for attempt in range(max_retries):
        try:
            # Scrape the URL
            # formats=["markdown"] tells FireCrawl to return clean markdown
            result = client.scrape(url, formats=["markdown"])
            
            # If we get here, scraping succeeded!
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # ============================================
            # ERROR CLASSIFICATION - Different errors need different responses
            # ============================================
            
            # CRITICAL: API credits exhausted (402 Payment Required)
            if "402" in error_msg or "payment" in error_msg.lower() or "credits" in error_msg.lower():
                print(f"\n[CRITICAL] API Credits Exhausted!")
                print(f"[INFO] Scraped successfully before this error")
                print(f"[ACTION] Upgrade at: https://firecrawl.dev/pricing")
                print(f"[ACTION] Then run this script again to resume")
                # Raise special exception to stop scraping
                raise Exception("CREDITS_EXHAUSTED")
            
            # Rate limit (429 Too Many Requests or "Rate Limit Exceeded")
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                # Extract wait time from error message if available
                import re
                wait_match = re.search(r'retry after (\d+)s', error_msg)
                if wait_match:
                    wait_time = int(wait_match.group(1)) + 2  # Add 2 seconds buffer
                else:
                    wait_time = 30 * (attempt + 1)  # Exponential backoff
                
                print(f"[WARN] Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue  # Try again
            
            # Timeout or network error
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                print(f"[WARN] Network error. Retry {attempt + 1}/{max_retries}")
                time.sleep(5)  # Wait 5 seconds
                continue  # Try again
            
            # Other errors
            else:
                print(f"[ERROR] {error_msg}")
                # If this is the last retry, give up
                if attempt == max_retries - 1:
                    print(f"[SKIP] Failed after {max_retries} attempts")
                    return None
                # Otherwise, wait and try again
                time.sleep(2)
                continue
    
    # If we get here, all retries failed
    return None


def save_to_database(conn, url, category, result):
    """
    Save scraped content to database.
    
    WHAT THIS TEACHES:
    - SQL INSERT statements
    - Parameterized queries (prevents SQL injection)
    - ON CONFLICT handling (upsert pattern)
    - JSON data in PostgreSQL
    - Database transactions
    
    Args:
        conn: Database connection
        url: Page URL
        category: Page category
        result: Scraped data from FireCrawl
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    
    try:
        # Create cursor
        cursor = conn.cursor()
        
        # Extract data from FireCrawl result
        # hasattr() checks if object has an attribute
        markdown_content = result.markdown if hasattr(result, 'markdown') else ''
        metadata = result.metadata if hasattr(result, 'metadata') else None
        
        # Extract metadata fields
        title = metadata.title if metadata and hasattr(metadata, 'title') else ''
        description = metadata.description if metadata and hasattr(metadata, 'description') else ''
        
        # Calculate content metrics
        content_length = len(markdown_content)
        # Estimate chunks: ~2400 chars per chunk (600 tokens * 4 chars/token)
        estimated_chunks = max(1, content_length // 2400)
        
        # Prepare metadata as JSON
        # Convert metadata object to dictionary for storage
        metadata_dict = {
            'title': title,
            'description': description,
            'language': metadata.language if metadata and hasattr(metadata, 'language') else 'en',
            'status_code': metadata.status_code if metadata and hasattr(metadata, 'status_code') else 200,
        }
        
        # SQL INSERT statement
        # %s are placeholders - psycopg2 will safely insert values
        # This prevents SQL injection attacks
        insert_query = """
        INSERT INTO documents 
            (url, title, description, category, markdown_content, 
             content_length, estimated_chunks, metadata, scraped_at)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            markdown_content = EXCLUDED.markdown_content,
            updated_at = NOW();
        """
        
        # Execute INSERT with actual values
        # Json() converts Python dict to PostgreSQL JSON
        cursor.execute(insert_query, (
            url,
            title,
            description,
            category,
            markdown_content,
            content_length,
            estimated_chunks,
            Json(metadata_dict),
            datetime.now()
        ))
        
        # Commit the transaction
        # This makes the change permanent in the database
        conn.commit()
        
        cursor.close()
        return True
        
    except Exception as e:
        # If something went wrong, rollback the transaction
        # This undoes any changes made in this transaction
        conn.rollback()
        print(f"[ERROR] Failed to save to database: {e}")
        return False


def print_progress_bar(current, total, bar_length=40):
    """
    Print a progress bar to show scraping progress.
    
    WHAT THIS TEACHES:
    - String formatting
    - Mathematical calculations
    - Console output formatting
    
    Args:
        current: Current number completed
        total: Total number to complete
        bar_length: Length of progress bar in characters
    """
    
    # Calculate percentage
    percent = (current / total) * 100
    
    # Calculate how many blocks to fill
    filled = int(bar_length * current / total)
    
    # Create the bar
    # '█' = filled block, '░' = empty block
    bar = '█' * filled + '░' * (bar_length - filled)
    
    # Print with carriage return (\r) to overwrite same line
    # end='' prevents newline
    print(f'\r[{bar}] {percent:.1f}% ({current}/{total})', end='', flush=True)


# ============================================
# MAIN SCRAPING FUNCTION
# ============================================

def main():
    """
    Main function - orchestrates the entire scraping process.
    
    WHAT THIS TEACHES:
    - Program flow control
    - Combining multiple functions
    - Error handling at scale
    - Progress tracking
    - Summary reporting
    """
    
    print("\n" + "="*60)
    print("FIRECRAWL WEB SCRAPER - Stirling Chat MVP")
    print("="*60 + "\n")
    
    # ============================================
    # STEP 1: Validate API Key
    # ============================================
    print("[STEP 1] Validating API key...")
    
    if not FIRECRAWL_API_KEY:
        print("[ERROR] FIRECRAWL_API_KEY not found in .env file")
        print("[HELP] Add your API key to .env file")
        return
    
    print(f"[SUCCESS] API key found: {FIRECRAWL_API_KEY[:15]}...\n")
    
    
    # ============================================
    # STEP 2: Connect to Database
    # ============================================
    print("[STEP 2] Connecting to database...")
    
    conn = connect_to_database()
    if not conn:
        return  # Exit if connection failed
    
    print()
    
    
    # ============================================
    # STEP 3: Read URL Files
    # ============================================
    print("[STEP 3] Reading URL files...")
    
    url_data = read_url_files()
    
    if not url_data:
        print("[ERROR] No URLs found")
        return
    
    # Calculate total URLs
    total_urls = sum(len(urls) for urls in url_data.values())
    print(f"\n[INFO] Total URLs to process: {total_urls}\n")
    
    
    # ============================================
    # STEP 4: Check Already Scraped
    # ============================================
    print("[STEP 4] Checking for already scraped URLs...")
    
    scraped_urls = get_scraped_urls(conn)
    print(f"[INFO] Found {len(scraped_urls)} URLs already in database")
    
    # Calculate remaining URLs
    remaining_count = 0
    for category, urls in url_data.items():
        remaining = [url for url in urls if url not in scraped_urls]
        remaining_count += len(remaining)
    
    print(f"[INFO] Remaining to scrape: {remaining_count}\n")
    
    # If everything is already scraped
    if remaining_count == 0:
        print("[SUCCESS] All URLs already scraped!")
        conn.close()
        return
    
    # Auto-continue if in resume mode
    if len(scraped_urls) > 0:
        print("[RESUME MODE] Some URLs already scraped")
        print("[AUTO] Continuing with remaining URLs...")
        print()
    
    
    # ============================================
    # STEP 5: Initialize FireCrawl Client
    # ============================================
    print("[STEP 5] Initializing FireCrawl client...")
    
    try:
        client = Firecrawl(api_key=FIRECRAWL_API_KEY)
        print("[SUCCESS] FireCrawl client ready\n")
    except Exception as e:
        print(f"[ERROR] Failed to initialize FireCrawl: {e}")
        conn.close()
        return
    
    
    # ============================================
    # STEP 6: Start Scraping
    # ============================================
    print("[STEP 6] Starting scraping process...\n")
    print("="*60)
    
    # Statistics tracking
    stats = {
        'total': remaining_count,
        'completed': 0,
        'skipped': 0,
        'errors': 0,
        'start_time': time.time()
    }
    
    # Process each category
    for category, urls in url_data.items():
        
        print(f"\n[CATEGORY] {category.upper()}")
        print("-" * 60)
        
        # Filter to only unscraped URLs
        urls_to_scrape = [url for url in urls if url not in scraped_urls]
        
        if not urls_to_scrape:
            print(f"[SKIP] All {len(urls)} URLs already scraped\n")
            continue
        
        print(f"[INFO] Processing {len(urls_to_scrape)}/{len(urls)} URLs\n")
        
        # Scrape each URL
        for i, url in enumerate(urls_to_scrape, 1):
            
            # Show progress
            print(f"[{i}/{len(urls_to_scrape)}] {url[:60]}...")
            
            try:
                # Scrape the URL
                result = scrape_url_with_retry(client, url)
                
                if result:
                    # Save to database
                    success = save_to_database(conn, url, category, result)
                    
                    if success:
                        stats['completed'] += 1
                        print(f"  [OK] Saved ({len(result.markdown):,} chars)")
                    else:
                        stats['errors'] += 1
                        print(f"  [ERROR] Failed to save")
                else:
                    stats['skipped'] += 1
                    print(f"  [SKIP] Failed to scrape")
                
            except Exception as e:
                # Check if credits exhausted
                if "CREDITS_EXHAUSTED" in str(e):
                    print(f"\n[STOPPED] Scraping stopped due to credit exhaustion")
                    print(f"[PROGRESS] Saved: {stats['completed']}/{stats['total']}")
                    break
                else:
                    stats['errors'] += 1
                    print(f"  [ERROR] {e}")
            
            # Delay between requests (be polite to server)
            if i < len(urls_to_scrape):
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Check if we should stop (credits exhausted)
        if stats['completed'] + stats['skipped'] + stats['errors'] < stats['total']:
            break
    
    
    # ============================================
    # STEP 7: Summary Report
    # ============================================
    elapsed_time = time.time() - stats['start_time']
    
    print("\n" + "="*60)
    print("SCRAPING COMPLETE - SUMMARY")
    print("="*60)
    print(f"\nTotal URLs to scrape: {stats['total']}")
    print(f"Successfully scraped: {stats['completed']}")
    print(f"Skipped (errors): {stats['skipped']}")
    print(f"Database errors: {stats['errors']}")
    print(f"Time elapsed: {elapsed_time/60:.1f} minutes")
    
    if stats['completed'] > 0:
        print(f"Average speed: {stats['completed']/(elapsed_time/60):.1f} URLs/minute")
    
    print("\n[SUCCESS] Data saved to PostgreSQL database")
    print("[INFO] View in pgAdmin or run queries to see results")
    print()
    
    # Close database connection
    conn.close()


# ============================================
# SCRIPT ENTRY POINT
# ============================================

if __name__ == "__main__":
    """
    This runs when script is executed directly.
    
    WHAT THIS TEACHES:
    - Python script entry points
    - if __name__ == "__main__" pattern
    """
    
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\n[CANCELLED] Scraping cancelled by user (Ctrl+C)")
        print("[INFO] Progress has been saved to database")
    except Exception as e:
        # Catch any unexpected errors
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
