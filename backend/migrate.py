#!/usr/bin/env python3
"""
Database Migration Script for Railway.app
Sets up PostgreSQL with pgvector extension and all required tables
COMPLETE VERSION - 13 Tables Total
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Setup database with pgvector extension and complete schema"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Installing pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # ============================================
        # TABLE 1: DOCUMENTS
        # ============================================
        print("Creating documents table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_url TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                full_content TEXT NOT NULL,
                crawled_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB
            );
        """)
        
        # ============================================
        # TABLE 2: CHUNKS
        # ============================================
        print("Creating chunks table with vector support...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),
                token_count INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # ============================================
        # TABLE 3: CONVERSATIONS
        # ============================================
        print("Creating conversations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                student_type VARCHAR(50),
                student_level VARCHAR(50),
                detected_location VARCHAR(100),
                programs_discussed TEXT[],
                lead_captured BOOLEAN DEFAULT FALSE,
                user_name VARCHAR(255),
                name_asked BOOLEAN DEFAULT FALSE,
                lead_capture_completeness INTEGER DEFAULT 0,
                ip_address VARCHAR(45),
                user_agent TEXT
            );
        """)
        
        # Add missing columns if table already exists
        print("Adding missing columns to conversations table if needed...")
        alter_statements = [
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS detected_location VARCHAR(100)",
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_name VARCHAR(255)",
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS name_asked BOOLEAN DEFAULT FALSE",
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS lead_capture_completeness INTEGER DEFAULT 0"
        ]
        for stmt in alter_statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Column may already exist: {e}")
        
        # ============================================
        # TABLE 4: MESSAGES
        # ============================================
        print("Creating messages table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                intent VARCHAR(100),
                confidence DOUBLE PRECISION,
                search_results JSONB,
                sources TEXT[],
                search_quality_score DOUBLE PRECISION,
                processing_time_ms INTEGER,
                tokens_used INTEGER,
                flagged BOOLEAN DEFAULT FALSE,
                flag_reason VARCHAR(255)
            );
        """)
        
        # ============================================
        # TABLE 5: CONVERSATION_FEEDBACK
        # ============================================
        print("Creating conversation_feedback table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_feedback (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                session_id VARCHAR(255) NOT NULL,
                rating VARCHAR(20) NOT NULL,
                suggestion TEXT,
                submitted_at TIMESTAMP DEFAULT NOW(),
                user_ip_address VARCHAR(45),
                user_agent TEXT,
                reviewed BOOLEAN DEFAULT FALSE
            );
        """)
        
        # ============================================
        # TABLE 6: SAFETY_INCIDENTS
        # ============================================
        print("Creating safety_incidents table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS safety_incidents (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                session_id VARCHAR(255),
                incident_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                input_hash VARCHAR(64),
                detected_patterns TEXT[],
                detected_at TIMESTAMP DEFAULT NOW(),
                response_action VARCHAR(100),
                reviewed BOOLEAN DEFAULT FALSE,
                reviewed_by VARCHAR(255),
                reviewed_at TIMESTAMP,
                notes TEXT
            );
        """)
        
        # ============================================
        # TABLE 7: CONVERSATION_CONTEXT
        # ============================================
        print("Creating conversation_context table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_context (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                context_key VARCHAR(100) NOT NULL,
                context_value JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # ============================================
        # TABLE 8: LEADS
        # ============================================
        print("Creating leads table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                location VARCHAR(255),
                student_type VARCHAR(50),
                student_level VARCHAR(50),
                programs_interested TEXT[],
                preferred_intake VARCHAR(50),
                topics_discussed TEXT[],
                captured_at TIMESTAMP DEFAULT NOW(),
                transcript_sent BOOLEAN DEFAULT FALSE,
                transcript_sent_at TIMESTAMP,
                follow_up_email_sent BOOLEAN DEFAULT FALSE,
                follow_up_email_sent_at TIMESTAMP,
                exported_to_crm BOOLEAN DEFAULT FALSE,
                crm_id VARCHAR(255),
                lead_quality_score INTEGER,
                escalation_reason TEXT,
                conversation_summary TEXT,
                user_query TEXT,
                last_messages JSONB,
                phone_country_code VARCHAR(10),
                nationality VARCHAR(100),
                country VARCHAR(100),
                capture_source JSONB
            );
        """)
        
        # ============================================
        # TABLE 9: LEAD_CAPTURE_TRACKING
        # ============================================
        print("Creating lead_capture_tracking table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_capture_tracking (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER UNIQUE REFERENCES conversations(id) ON DELETE CASCADE,
                session_id VARCHAR(255) NOT NULL,
                name_captured BOOLEAN DEFAULT FALSE,
                email_captured BOOLEAN DEFAULT FALSE,
                phone_captured BOOLEAN DEFAULT FALSE,
                country_captured BOOLEAN DEFAULT FALSE,
                program_captured BOOLEAN DEFAULT FALSE,
                level_captured BOOLEAN DEFAULT FALSE,
                name_captured_at TIMESTAMP,
                name_source VARCHAR(50),
                email_captured_at TIMESTAMP,
                email_source VARCHAR(50),
                phone_captured_at TIMESTAMP,
                phone_source VARCHAR(50),
                country_captured_at TIMESTAMP,
                country_source VARCHAR(50),
                program_captured_at TIMESTAMP,
                program_source VARCHAR(50),
                level_captured_at TIMESTAMP,
                level_source VARCHAR(50),
                missing_fields TEXT[],
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # ============================================
        # TABLE 10: PHONE_COUNTRY_CODES
        # ============================================
        print("Creating phone_country_codes table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phone_country_codes (
                id SERIAL PRIMARY KEY,
                country_code VARCHAR(10) UNIQUE NOT NULL,
                country_name VARCHAR(100) NOT NULL,
                country_iso VARCHAR(3),
                region VARCHAR(50)
            );
        """)
        
        # ============================================
        # TABLE 11: RATE_LIMIT_TRACKING
        # ============================================
        print("Creating rate_limit_tracking table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit_tracking (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255),
                ip_address INET,
                message_count INTEGER DEFAULT 0,
                first_message_at TIMESTAMP DEFAULT NOW(),
                last_message_at TIMESTAMP DEFAULT NOW(),
                window_start TIMESTAMP DEFAULT NOW(),
                UNIQUE(session_id, window_start)
            );
        """)
        
        # ============================================
        # TABLE 12: SCHEMA_VERSION
        # ============================================
        print("Creating schema_version table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version VARCHAR(20) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT NOW(),
                description TEXT
            );
        """)
        
        # Insert current schema version
        cursor.execute("""
            INSERT INTO schema_version (version, description)
            VALUES ('1.0.0', 'Initial complete schema with all 13 tables')
            ON CONFLICT (version) DO NOTHING;
        """)
        
        # ============================================
        # INDEXES
        # ============================================
        print("Creating indexes...")
        
        # Vector similarity index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
            ON chunks USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
        
        # Document indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS documents_category_idx ON documents(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS documents_url_idx ON documents(source_url);")
        
        # Conversation indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS conversations_session_id_idx ON conversations(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS conversations_created_at_idx ON conversations(created_at);")
        
        # Message indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS messages_conversation_id_idx ON messages(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS messages_created_at_idx ON messages(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS messages_role_idx ON messages(role);")
        cursor.execute("CREATE INDEX IF NOT EXISTS messages_intent_idx ON messages(intent);")
        
        # Feedback indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS conversation_feedback_conversation_id_idx ON conversation_feedback(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS conversation_feedback_rating_idx ON conversation_feedback(rating);")
        cursor.execute("CREATE INDEX IF NOT EXISTS conversation_feedback_reviewed_idx ON conversation_feedback(reviewed);")
        
        # Safety incident indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS safety_incidents_conversation_id_idx ON safety_incidents(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS safety_incidents_detected_at_idx ON safety_incidents(detected_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS safety_incidents_incident_type_idx ON safety_incidents(incident_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS safety_incidents_severity_idx ON safety_incidents(severity);")
        cursor.execute("CREATE INDEX IF NOT EXISTS safety_incidents_reviewed_idx ON safety_incidents(reviewed);")
        
        # Conversation context indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS conversation_context_conversation_id_idx ON conversation_context(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS conversation_context_key_idx ON conversation_context(context_key);")
        
        # Leads indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS leads_email_idx ON leads(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS leads_captured_at_idx ON leads(captured_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS leads_student_type_idx ON leads(student_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS leads_transcript_sent_idx ON leads(transcript_sent);")
        
        # Lead capture tracking indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS lead_capture_tracking_conversation_idx ON lead_capture_tracking(conversation_id);")
        
        # Phone country codes indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS phone_country_codes_code_idx ON phone_country_codes(country_code);")
        
        # Rate limit tracking indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS rate_limit_session_id_idx ON rate_limit_tracking(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS rate_limit_ip_address_idx ON rate_limit_tracking(ip_address);")
        cursor.execute("CREATE INDEX IF NOT EXISTS rate_limit_window_start_idx ON rate_limit_tracking(window_start);")
        
        print("Database setup complete!")
        
        # Check table counts
        cursor.execute("SELECT COUNT(*) FROM documents;")
        doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chunks;")
        chunk_count = cursor.fetchone()[0]
        
        print(f"Database stats:")
        print(f"   - Documents: {doc_count}")
        print(f"   - Chunks: {chunk_count}")
        print(f"   - Total tables created: 13")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Railway database migration...")
    success = setup_database()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed - check logs above")
        sys.exit(1)
