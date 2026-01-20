#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract complete CREATE TABLE statements from local PostgreSQL database
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def extract_table_schema(cursor, table_name):
    """Extract complete CREATE TABLE statement for a table"""
    
    # Get columns with full details
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = cursor.fetchall()
    
    # Get primary key
    cursor.execute("""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass AND i.indisprimary;
    """, (table_name,))
    
    pk_columns = [row[0] for row in cursor.fetchall()]
    
    # Get foreign keys
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
            AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = %s
        AND tc.table_schema = 'public';
    """, (table_name,))
    
    foreign_keys = cursor.fetchall()
    
    # Build CREATE TABLE statement
    create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    col_definitions = []
    for col in columns:
        col_name = col[0]
        data_type = col[1]
        max_length = col[2]
        precision = col[3]
        scale = col[4]
        nullable = col[5]
        default = col[6]
        
        # Build column definition
        col_def = f"    {col_name} "
        
        # Handle data type
        if data_type == 'character varying':
            col_def += f"VARCHAR({max_length})" if max_length else "VARCHAR(255)"
        elif data_type == 'ARRAY':
            col_def += "TEXT[]"
        elif data_type == 'timestamp without time zone':
            col_def += "TIMESTAMP"
        elif data_type == 'USER-DEFINED':
            # Check if it's a vector type
            cursor.execute("""
                SELECT udt_name FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (table_name, col_name))
            udt = cursor.fetchone()
            if udt and 'vector' in str(udt[0]):
                col_def += "vector(1536)"
            else:
                col_def += data_type.upper()
        else:
            col_def += data_type.upper()
        
        # Handle NOT NULL
        if nullable == 'NO':
            col_def += " NOT NULL"
        
        # Handle DEFAULT
        if default:
            if 'nextval' in default:
                # Skip SERIAL defaults
                pass
            elif default == 'CURRENT_TIMESTAMP' or 'now()' in default:
                col_def += " DEFAULT NOW()"
            elif default == 'false':
                col_def += " DEFAULT FALSE"
            elif default == 'true':
                col_def += " DEFAULT TRUE"
            elif default.startswith("'"):
                col_def += f" DEFAULT {default}"
            else:
                col_def += f" DEFAULT {default}"
        
        col_definitions.append(col_def)
    
    create_stmt += ",\n".join(col_definitions)
    
    # Add primary key
    if pk_columns:
        create_stmt += f",\n    PRIMARY KEY ({', '.join(pk_columns)})"
    
    # Add foreign keys
    for fk in foreign_keys:
        col_name, ref_table, ref_col, delete_rule = fk
        on_delete = f" ON DELETE {delete_rule}" if delete_rule != 'NO ACTION' else ""
        create_stmt += f",\n    FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col}){on_delete}"
    
    create_stmt += "\n);"
    
    return create_stmt

def extract_indexes(cursor, table_name):
    """Extract CREATE INDEX statements for a table"""
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = %s
        AND indexname NOT LIKE '%_pkey'
        ORDER BY indexname;
    """, (table_name,))
    
    indexes = cursor.fetchall()
    index_stmts = []
    
    for idx_name, idx_def in indexes:
        # Convert to CREATE INDEX IF NOT EXISTS
        idx_def = idx_def.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
        index_stmts.append(idx_def + ';')
    
    return index_stmts

def main():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Tables to extract (missing from migrate.py)
        missing_tables = [
            'conversation_context',
            'conversation_feedback',
            'lead_capture_tracking',
            'leads',
            'phone_country_codes',
            'rate_limit_tracking',
            'schema_version'
        ]
        
        print("="*70)
        print("COMPLETE SCHEMA EXTRACTION FOR MISSING TABLES")
        print("="*70)
        
        for table in missing_tables:
            print(f"\n\n-- {table.upper()} TABLE")
            print("-" * 70)
            
            # Extract CREATE TABLE
            create_stmt = extract_table_schema(cursor, table)
            print(create_stmt)
            
            # Extract indexes
            indexes = extract_indexes(cursor, table)
            if indexes:
                print(f"\n-- Indexes for {table}")
                for idx in indexes:
                    print(idx)
        
        cursor.close()
        conn.close()
        
        print("\n\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
