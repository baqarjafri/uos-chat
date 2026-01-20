#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check local PostgreSQL database schema
Compare with migrate.py to identify any missing tables
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def check_database_schema():
    """Check all tables in the database"""
    
    try:
        print("Connecting to local PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all user tables (excluding system tables)
        print("\nListing all tables in database:\n")
        cursor.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database!")
            return
        
        print(f"Found {len(tables)} tables:\n")
        print("-" * 60)
        
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table['table_name']:30} | Size: {table['size']}")
        
        print("-" * 60)
        
        # Get detailed schema for each table
        print("\n\nDetailed Table Schemas:\n")
        
        for table in tables:
            table_name = table['table_name']
            print(f"\n{'='*60}")
            print(f"Table: {table_name}")
            print('='*60)
            
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            print("\nColumns:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                print(f"  - {col['column_name']:25} {col['data_type']}{length:15} {nullable}")
            
            # Get indexes
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s;
            """, (table_name,))
            
            indexes = cursor.fetchall()
            
            if indexes:
                print("\nIndexes:")
                for idx in indexes:
                    print(f"  - {idx['indexname']}")
        
        # Compare with migrate.py expected tables
        print("\n\n" + "="*60)
        print("COMPARISON WITH MIGRATE.PY")
        print("="*60)
        
        expected_tables = [
            'documents',
            'chunks',
            'conversations',
            'messages',
            'feedback',
            'safety_incidents'
        ]
        
        actual_table_names = [t['table_name'] for t in tables]
        
        print("\nExpected tables in migrate.py:")
        for table in expected_tables:
            status = "[EXISTS]" if table in actual_table_names else "[MISSING]"
            print(f"  {table:25} {status}")
        
        print("\nAdditional tables not in migrate.py:")
        extra_tables = [t for t in actual_table_names if t not in expected_tables]
        if extra_tables:
            for table in extra_tables:
                print(f"  - {table}")
        else:
            print("  None")
        
        cursor.close()
        conn.close()
        
        print("\nDatabase schema check complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_schema()
