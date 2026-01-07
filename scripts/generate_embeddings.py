"""
Generate Embeddings for Stirling Chat MVP
=========================================

PURPOSE:
    Generate vector embeddings for all chunks using OpenAI's text-embedding-3-small
    
FEATURES:
    - Batch processing (100 chunks at a time)
    - Rate limiting (respects API limits)
    - Resume capability (skips already embedded chunks)
    - Progress tracking with tqdm
    - Error handling with retry logic
    - Cost tracking (real-time)
    - Embedding validation
    
USAGE:
    python scripts/generate_embeddings.py
    
OUTPUT:
    - Embeddings stored in chunks.embedding column
    - Summary report with costs and statistics
    
REQUIREMENTS:
    - OpenAI API key in .env
    - Chunks already created in database
    
Author: Stirling Chat Team
Date: November 18, 2025
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
import openai
from tqdm import tqdm
import numpy as np

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', 1536))

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'stirling_chat'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

# Batch processing configuration
BATCH_SIZE = 100              # Process 100 chunks at a time
RATE_LIMIT_DELAY = 1.0        # 1 second delay between batches
MAX_RETRIES = 3               # Retry failed chunks up to 3 times
RETRY_DELAY = 2.0             # 2 seconds between retries

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY


def estimate_cost(total_tokens):
    """
    Estimate embedding cost
    
    Args:
        total_tokens (int): Total tokens to embed
        
    Returns:
        float: Estimated cost in USD
    """
    # text-embedding-3-small: $0.02 per 1M tokens
    cost_per_million = 0.02
    return (total_tokens / 1_000_000) * cost_per_million


def generate_embeddings_batch(texts, retry_count=0):
    """
    Generate embeddings for a batch of texts
    
    Args:
        texts (list): List of text strings to embed
        retry_count (int): Current retry attempt
        
    Returns:
        list: List of embedding vectors
        
    Raises:
        Exception: If all retries fail
    """
    try:
        response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS
        )
        
        embeddings = [item.embedding for item in response.data]
        return embeddings
        
    except openai.RateLimitError as e:
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
            print(f"\n⚠️  Rate limit hit. Waiting {wait_time}s before retry {retry_count + 1}/{MAX_RETRIES}...")
            time.sleep(wait_time)
            return generate_embeddings_batch(texts, retry_count + 1)
        else:
            raise Exception(f"Rate limit error after {MAX_RETRIES} retries: {e}")
    
    except openai.APIError as e:
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_DELAY * (2 ** retry_count)
            print(f"\n⚠️  API error. Waiting {wait_time}s before retry {retry_count + 1}/{MAX_RETRIES}...")
            time.sleep(wait_time)
            return generate_embeddings_batch(texts, retry_count + 1)
        else:
            raise Exception(f"API error after {MAX_RETRIES} retries: {e}")
    
    except Exception as e:
        raise Exception(f"Unexpected error generating embeddings: {e}")


def validate_embedding(embedding, chunk_id):
    """
    Validate embedding vector
    
    Args:
        embedding (list): Embedding vector
        chunk_id (int): Chunk ID for error reporting
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check dimensions
    if len(embedding) != EMBEDDING_DIMENSIONS:
        print(f"\n⚠️  Warning: Chunk {chunk_id} has {len(embedding)} dimensions, expected {EMBEDDING_DIMENSIONS}")
        return False
    
    # Check if all values are numbers
    if not all(isinstance(x, (int, float)) for x in embedding):
        print(f"\n⚠️  Warning: Chunk {chunk_id} has non-numeric values")
        return False
    
    # Check norm (should be close to 1.0 for normalized embeddings)
    norm = np.linalg.norm(embedding)
    if not (0.95 < norm < 1.05):
        print(f"\n⚠️  Warning: Chunk {chunk_id} has unusual norm: {norm:.3f}")
        # Don't fail, just warn
    
    return True


def process_embeddings():
    """
    Main embedding generation process
    
    Workflow:
    1. Connect to database
    2. Get chunks without embeddings
    3. Estimate cost
    4. Process in batches
    5. Validate and store embeddings
    6. Generate summary report
    """
    
    print("\n" + "="*70)
    print("EMBEDDING GENERATION - OpenAI text-embedding-3-small")
    print("="*70 + "\n")
    
    # Verify API key
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    print(f"⚙️  Configuration:")
    print(f"   Model: {EMBEDDING_MODEL}")
    print(f"   Dimensions: {EMBEDDING_DIMENSIONS}")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Rate limit delay: {RATE_LIMIT_DELAY}s\n")
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"✅ Connected to database: {DB_CONFIG['database']}\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Get chunks without embeddings
    cursor.execute("""
        SELECT id, content, token_count
        FROM chunks
        WHERE embedding IS NULL
        ORDER BY id;
    """)
    
    chunks_to_embed = cursor.fetchall()
    total_chunks = len(chunks_to_embed)
    
    if total_chunks == 0:
        print("✅ All chunks already have embeddings!")
        print("   Nothing to do.\n")
        cursor.close()
        conn.close()
        return
    
    # Get total chunks for progress
    cursor.execute("SELECT COUNT(*) FROM chunks;")
    total_chunks_db = cursor.fetchone()[0]
    already_embedded = total_chunks_db - total_chunks
    
    print(f"📊 Embedding Status:")
    print(f"   Total chunks: {total_chunks_db:,}")
    print(f"   Already embedded: {already_embedded:,}")
    print(f"   To embed: {total_chunks:,}\n")
    
    # Estimate cost
    total_tokens = sum(chunk[2] for chunk in chunks_to_embed)
    estimated_cost = estimate_cost(total_tokens)
    
    print(f"💰 Cost Estimate:")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Estimated cost: ${estimated_cost:.4f}")
    print(f"   Model: {EMBEDDING_MODEL} ($0.02 per 1M tokens)\n")
    
    # Confirm before proceeding
    print(f"⏱️  Estimated time: {(total_chunks / BATCH_SIZE) * RATE_LIMIT_DELAY / 60:.1f} minutes\n")
    
    print("🚀 Starting embedding generation...\n")
    
    # Process in batches
    successful = 0
    failed = 0
    total_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    
    start_time = time.time()
    
    for batch_idx in tqdm(range(0, total_chunks, BATCH_SIZE), 
                          desc="Generating embeddings", 
                          unit="batch",
                          total=total_batches):
        
        batch = chunks_to_embed[batch_idx:batch_idx + BATCH_SIZE]
        chunk_ids = [chunk[0] for chunk in batch]
        texts = [chunk[1] for chunk in batch]
        
        try:
            # Generate embeddings for batch
            embeddings = generate_embeddings_batch(texts)
            
            # Validate embeddings
            valid_embeddings = []
            for i, (chunk_id, embedding) in enumerate(zip(chunk_ids, embeddings)):
                if validate_embedding(embedding, chunk_id):
                    valid_embeddings.append((chunk_id, embedding))
                else:
                    failed += 1
            
            # Store embeddings in database
            if valid_embeddings:
                execute_batch(cursor, """
                    UPDATE chunks
                    SET embedding = %s::vector
                    WHERE id = %s
                """, [(embedding, chunk_id) for chunk_id, embedding in valid_embeddings])
                
                conn.commit()
                successful += len(valid_embeddings)
            
            # Rate limiting (except for last batch)
            if batch_idx + BATCH_SIZE < total_chunks:
                time.sleep(RATE_LIMIT_DELAY)
        
        except Exception as e:
            print(f"\n❌ Error processing batch {batch_idx // BATCH_SIZE + 1}: {e}")
            failed += len(batch)
            conn.rollback()
            continue
    
    elapsed_time = time.time() - start_time
    
    # Generate summary report
    print("\n\n" + "="*70)
    print("EMBEDDING GENERATION SUMMARY")
    print("="*70 + "\n")
    
    # Get final statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
            COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings
        FROM chunks;
    """)
    
    stats = cursor.fetchone()
    total, with_embeddings, without_embeddings = stats
    
    print(f"✅ Successfully embedded: {successful:,} chunks")
    if failed > 0:
        print(f"❌ Failed: {failed:,} chunks")
    print(f"📊 Total with embeddings: {with_embeddings:,} / {total:,} ({with_embeddings/total*100:.1f}%)")
    
    if without_embeddings > 0:
        print(f"⚠️  Still missing embeddings: {without_embeddings:,}")
    
    # Cost calculation
    actual_tokens = sum(chunk[2] for chunk in chunks_to_embed[:successful])
    actual_cost = estimate_cost(actual_tokens)
    
    print(f"\n💰 Actual Cost:")
    print(f"   Tokens processed: {actual_tokens:,}")
    print(f"   Cost: ${actual_cost:.4f}")
    
    print(f"\n⏱️  Performance:")
    print(f"   Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
    print(f"   Chunks per second: {successful/elapsed_time:.1f}")
    print(f"   Average batch time: {elapsed_time/total_batches:.2f}s")
    
    print(f"\n💾 Database: chunks.embedding column updated")
    print(f"⏰ Completed at: {datetime.now().strftime('%I:%M:%S %p')}\n")
    
    # Index status
    print("="*70)
    print("INDEX STATUS")
    print("="*70)
    print("✅ HNSW index will be automatically updated")
    print("   Index type: hnsw (m=16, ef_construction=64)")
    print("   Distance metric: cosine similarity")
    print("   No manual rebuild needed!\n")
    
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Test vector search: python scripts/test_search.py")
    print("2. Build RAG system: python scripts/query_rag.py")
    print("3. Create API backend: python scripts/run_api.py\n")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        process_embeddings()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
