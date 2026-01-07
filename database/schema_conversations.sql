-- ============================================
-- CONVERSATIONAL RAG SYSTEM - DATABASE SCHEMA
-- ============================================
-- Purpose: Store conversation history, messages, leads, and safety incidents
-- Version: 2.0 (Enhanced with guardrails and student profiling)
-- Created: 2025-11-20
-- ============================================

-- ============================================
-- 1. CONVERSATIONS TABLE
-- ============================================
-- Stores conversation sessions with metadata
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- Student Profile (detected during conversation)
    student_type VARCHAR(50),  -- scottish, uk, eu, international, unknown
    student_level VARCHAR(50), -- undergraduate, postgraduate, phd, unknown
    detected_location VARCHAR(255), -- Country/region mentioned
    
    -- Conversation Metadata
    total_messages INTEGER DEFAULT 0,
    programs_discussed TEXT[], -- Array of program names
    topics_covered TEXT[],     -- Array of topics (fees, requirements, etc.)
    
    -- Lead Status
    lead_captured BOOLEAN DEFAULT FALSE,
    lead_id INTEGER,
    
    -- Quality Metrics
    avg_response_time_ms INTEGER,
    user_satisfaction_score INTEGER, -- 1-5 rating if collected
    
    -- Safety Flags
    flagged_for_review BOOLEAN DEFAULT FALSE,
    safety_incidents_count INTEGER DEFAULT 0,
    
    -- Indexes for performance
    CONSTRAINT valid_student_type CHECK (
        student_type IN ('scottish', 'uk', 'eu', 'international', 'unknown', NULL)
    ),
    CONSTRAINT valid_student_level CHECK (
        student_level IN ('undergraduate', 'postgraduate', 'phd', 'unknown', NULL)
    )
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_student_type ON conversations(student_type);
CREATE INDEX idx_conversations_lead_captured ON conversations(lead_captured);

-- ============================================
-- 2. MESSAGES TABLE
-- ============================================
-- Stores individual messages in conversations
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message Content
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Message Metadata
    intent VARCHAR(100),       -- Detected intent (program_inquiry, fee_question, etc.)
    confidence FLOAT,          -- Intent confidence score
    
    -- RAG Metadata (for assistant messages)
    search_results JSONB,      -- Search results used
    sources TEXT[],            -- Source URLs cited
    search_quality_score FLOAT, -- Quality of search results
    
    -- Processing Metadata
    processing_time_ms INTEGER, -- Time to generate response
    tokens_used INTEGER,        -- Tokens consumed
    
    -- Safety Flags
    flagged BOOLEAN DEFAULT FALSE,
    flag_reason VARCHAR(255),
    
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant'))
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_intent ON messages(intent);

-- ============================================
-- 3. LEADS TABLE
-- ============================================
-- Stores captured lead information
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    
    -- Contact Information
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    
    -- Location & Profile
    location VARCHAR(255),     -- Country/region
    student_type VARCHAR(50),  -- scottish, uk, eu, international
    student_level VARCHAR(50), -- undergraduate, postgraduate, phd
    
    -- Interest Information
    programs_interested TEXT[], -- Programs discussed
    preferred_intake VARCHAR(50), -- e.g., "September 2025"
    topics_discussed TEXT[],    -- Topics covered in conversation
    
    -- Timestamps
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Follow-up Status
    transcript_sent BOOLEAN DEFAULT FALSE,
    transcript_sent_at TIMESTAMP,
    follow_up_email_sent BOOLEAN DEFAULT FALSE,
    follow_up_email_sent_at TIMESTAMP,
    
    -- CRM Integration
    exported_to_crm BOOLEAN DEFAULT FALSE,
    crm_id VARCHAR(255),
    
    -- Quality Score
    lead_quality_score INTEGER, -- 1-10 based on engagement
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_captured_at ON leads(captured_at);
CREATE INDEX idx_leads_student_type ON leads(student_type);
CREATE INDEX idx_leads_transcript_sent ON leads(transcript_sent);

-- ============================================
-- 4. SAFETY_INCIDENTS TABLE
-- ============================================
-- Logs safety incidents for monitoring and improvement
CREATE TABLE IF NOT EXISTS safety_incidents (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    session_id VARCHAR(255),
    
    -- Incident Details
    incident_type VARCHAR(100) NOT NULL, -- prompt_injection, harassment, off_topic, etc.
    severity VARCHAR(20) NOT NULL,       -- low, medium, high, critical
    
    -- Content (hashed for privacy)
    input_hash VARCHAR(64),              -- SHA-256 hash of user input
    detected_patterns TEXT[],            -- Patterns that triggered detection
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Response
    response_action VARCHAR(100),        -- redirect, warn, terminate, etc.
    
    -- Review Status
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    notes TEXT,
    
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_incident_type CHECK (
        incident_type IN (
            'prompt_injection', 'harassment', 'profanity', 'off_topic',
            'sensitive_data', 'spam', 'comparison_attempt', 'other'
        )
    )
);

CREATE INDEX idx_safety_incidents_conversation_id ON safety_incidents(conversation_id);
CREATE INDEX idx_safety_incidents_detected_at ON safety_incidents(detected_at);
CREATE INDEX idx_safety_incidents_incident_type ON safety_incidents(incident_type);
CREATE INDEX idx_safety_incidents_severity ON safety_incidents(severity);
CREATE INDEX idx_safety_incidents_reviewed ON safety_incidents(reviewed);

-- ============================================
-- 5. RATE_LIMIT_TRACKING TABLE
-- ============================================
-- Tracks rate limits per session and IP
CREATE TABLE IF NOT EXISTS rate_limit_tracking (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    ip_address INET,
    
    -- Tracking
    message_count INTEGER DEFAULT 1,
    first_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Window (for cleanup)
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, window_start)
);

CREATE INDEX idx_rate_limit_session_id ON rate_limit_tracking(session_id);
CREATE INDEX idx_rate_limit_ip_address ON rate_limit_tracking(ip_address);
CREATE INDEX idx_rate_limit_window_start ON rate_limit_tracking(window_start);

-- ============================================
-- 6. CONVERSATION_CONTEXT TABLE
-- ============================================
-- Stores conversation context for memory across turns
CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Context Data
    context_key VARCHAR(100) NOT NULL,   -- e.g., 'mentioned_programs', 'clarification_needed'
    context_value JSONB NOT NULL,        -- Flexible JSON storage
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(conversation_id, context_key)
);

CREATE INDEX idx_conversation_context_conversation_id ON conversation_context(conversation_id);
CREATE INDEX idx_conversation_context_key ON conversation_context(context_key);

-- ============================================
-- TRIGGERS
-- ============================================

-- Update conversations.updated_at on any change
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_on_message
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();

-- Increment message count on conversations
CREATE OR REPLACE FUNCTION increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET total_messages = total_messages + 1
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_message_count
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION increment_message_count();

-- Increment safety incidents count
CREATE OR REPLACE FUNCTION increment_safety_incidents()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET safety_incidents_count = safety_incidents_count + 1,
        flagged_for_review = CASE 
            WHEN NEW.severity IN ('high', 'critical') THEN TRUE 
            ELSE flagged_for_review 
        END
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_safety_incidents
AFTER INSERT ON safety_incidents
FOR EACH ROW
EXECUTE FUNCTION increment_safety_incidents();

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

-- Conversation summary view
CREATE OR REPLACE VIEW conversation_summary AS
SELECT 
    c.id,
    c.session_id,
    c.created_at,
    c.student_type,
    c.student_level,
    c.total_messages,
    c.lead_captured,
    c.safety_incidents_count,
    COUNT(DISTINCT m.id) as message_count,
    l.email as lead_email,
    l.name as lead_name
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
LEFT JOIN leads l ON c.lead_id = l.id
GROUP BY c.id, l.email, l.name;

-- Daily metrics view
CREATE OR REPLACE VIEW daily_metrics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_conversations,
    COUNT(*) FILTER (WHERE lead_captured = TRUE) as leads_captured,
    COUNT(*) FILTER (WHERE safety_incidents_count > 0) as conversations_with_incidents,
    ROUND(AVG(total_messages), 2) as avg_messages_per_conversation,
    COUNT(*) FILTER (WHERE student_type = 'scottish') as scottish_students,
    COUNT(*) FILTER (WHERE student_type = 'uk') as uk_students,
    COUNT(*) FILTER (WHERE student_type = 'international') as international_students
FROM conversations
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Safety incidents summary
CREATE OR REPLACE VIEW safety_summary AS
SELECT 
    incident_type,
    severity,
    COUNT(*) as incident_count,
    COUNT(*) FILTER (WHERE reviewed = TRUE) as reviewed_count,
    DATE(detected_at) as date
FROM safety_incidents
GROUP BY incident_type, severity, DATE(detected_at)
ORDER BY date DESC, incident_count DESC;

-- ============================================
-- CLEANUP FUNCTIONS
-- ============================================

-- Clean up old rate limit tracking (older than 1 hour)
CREATE OR REPLACE FUNCTION cleanup_old_rate_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM rate_limit_tracking 
    WHERE window_start < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE conversations IS 'Stores conversation sessions with student profiling and metadata';
COMMENT ON TABLE messages IS 'Individual messages with RAG metadata and safety flags';
COMMENT ON TABLE leads IS 'Captured lead information with follow-up tracking';
COMMENT ON TABLE safety_incidents IS 'Security and safety incident logging';
COMMENT ON TABLE rate_limit_tracking IS 'Rate limiting and spam prevention';
COMMENT ON TABLE conversation_context IS 'Conversation memory and context storage';

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- You can add any initial configuration data here

-- ============================================
-- SCHEMA VERSION TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- ============================================
-- 7. CONVERSATION FEEDBACK TABLE
-- ============================================
-- Stores user feedback for conversation quality improvement
CREATE TABLE IF NOT EXISTS conversation_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    
    -- Feedback Rating (3 levels)
    rating VARCHAR(20) NOT NULL CHECK (rating IN ('bad', 'average', 'good')),
    
    -- Optional Textual Suggestion
    suggestion TEXT,
    has_suggestion BOOLEAN DEFAULT FALSE,
    
    -- Feedback Context
    total_messages_in_conversation INTEGER,
    conversation_duration_seconds INTEGER,
    
    -- Categorization for Analysis
    feedback_categories TEXT[], -- e.g., ['response_quality', 'accuracy', 'helpfulness']
    
    -- Metadata
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip_address VARCHAR(45), -- For tracking (IPv4/IPv6)
    user_agent TEXT, -- Browser/device info
    
    -- Follow-up
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100),
    action_taken TEXT,
    
    -- Indexes
    CONSTRAINT unique_feedback_per_conversation UNIQUE (conversation_id)
);

-- Index for quick lookups
CREATE INDEX idx_feedback_rating ON conversation_feedback(rating);
CREATE INDEX idx_feedback_submitted_at ON conversation_feedback(submitted_at);
CREATE INDEX idx_feedback_reviewed ON conversation_feedback(reviewed);
CREATE INDEX idx_feedback_session ON conversation_feedback(session_id);

-- ============================================
-- 8. FEEDBACK ANALYTICS VIEWS
-- ============================================

-- Daily feedback summary
CREATE OR REPLACE VIEW daily_feedback_summary AS
SELECT 
    DATE(submitted_at) as feedback_date,
    rating,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE has_suggestion = TRUE) as with_suggestions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE has_suggestion = TRUE) / COUNT(*), 2) as suggestion_rate,
    AVG(total_messages_in_conversation) as avg_messages,
    AVG(conversation_duration_seconds) as avg_duration_seconds
FROM conversation_feedback
GROUP BY DATE(submitted_at), rating
ORDER BY feedback_date DESC, rating;

-- Overall feedback metrics
CREATE OR REPLACE VIEW feedback_metrics AS
SELECT 
    COUNT(*) as total_feedback,
    COUNT(*) FILTER (WHERE rating = 'good') as good_count,
    COUNT(*) FILTER (WHERE rating = 'average') as average_count,
    COUNT(*) FILTER (WHERE rating = 'bad') as bad_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE rating = 'good') / COUNT(*), 2) as good_percentage,
    ROUND(100.0 * COUNT(*) FILTER (WHERE rating = 'average') / COUNT(*), 2) as average_percentage,
    ROUND(100.0 * COUNT(*) FILTER (WHERE rating = 'bad') / COUNT(*), 2) as bad_percentage,
    COUNT(*) FILTER (WHERE has_suggestion = TRUE) as total_with_suggestions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE has_suggestion = TRUE) / COUNT(*), 2) as suggestion_rate
FROM conversation_feedback;

-- Feedback with conversation details
CREATE OR REPLACE VIEW feedback_with_context AS
SELECT 
    cf.id as feedback_id,
    cf.rating,
    cf.suggestion,
    cf.has_suggestion,
    cf.submitted_at,
    c.session_id,
    c.student_type,
    c.student_level,
    c.total_messages,
    c.programs_discussed,
    c.lead_captured,
    c.safety_incidents_count,
    cf.total_messages_in_conversation,
    cf.conversation_duration_seconds,
    cf.reviewed,
    cf.action_taken
FROM conversation_feedback cf
JOIN conversations c ON cf.conversation_id = c.id
ORDER BY cf.submitted_at DESC;

-- Unreviewed bad feedback (priority for review)
CREATE OR REPLACE VIEW unreviewed_bad_feedback AS
SELECT 
    cf.id as feedback_id,
    cf.conversation_id,
    cf.session_id,
    cf.suggestion,
    cf.submitted_at,
    c.student_type,
    c.total_messages,
    c.programs_discussed,
    c.safety_incidents_count
FROM conversation_feedback cf
JOIN conversations c ON cf.conversation_id = c.id
WHERE cf.rating = 'bad' 
  AND cf.reviewed = FALSE
ORDER BY cf.submitted_at DESC;

-- ============================================
-- 9. FEEDBACK TRIGGERS
-- ============================================

-- Update conversation when feedback is submitted
CREATE OR REPLACE FUNCTION update_conversation_on_feedback()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the conversation with satisfaction score
    UPDATE conversations
    SET 
        user_satisfaction_score = CASE 
            WHEN NEW.rating = 'good' THEN 5
            WHEN NEW.rating = 'average' THEN 3
            WHEN NEW.rating = 'bad' THEN 1
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    
    -- Flag for review if bad rating
    IF NEW.rating = 'bad' THEN
        UPDATE conversations
        SET flagged_for_review = TRUE
        WHERE id = NEW.conversation_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_on_feedback
    AFTER INSERT ON conversation_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_on_feedback();

-- ============================================
-- 10. FEEDBACK HELPER FUNCTIONS
-- ============================================

-- Function to get feedback statistics for a date range
CREATE OR REPLACE FUNCTION get_feedback_stats(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    total_feedback BIGINT,
    good_count BIGINT,
    average_count BIGINT,
    bad_count BIGINT,
    good_percentage NUMERIC,
    avg_messages NUMERIC,
    suggestion_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_feedback,
        COUNT(*) FILTER (WHERE rating = 'good') as good_count,
        COUNT(*) FILTER (WHERE rating = 'average') as average_count,
        COUNT(*) FILTER (WHERE rating = 'bad') as bad_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE rating = 'good') / COUNT(*), 2) as good_percentage,
        ROUND(AVG(total_messages_in_conversation), 2) as avg_messages,
        COUNT(*) FILTER (WHERE has_suggestion = TRUE) as suggestion_count
    FROM conversation_feedback
    WHERE DATE(submitted_at) BETWEEN start_date AND end_date;
END;
$$ LANGUAGE plpgsql;

-- Function to mark feedback as reviewed
CREATE OR REPLACE FUNCTION mark_feedback_reviewed(
    feedback_id INTEGER,
    reviewer_name VARCHAR(100),
    action_description TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE conversation_feedback
    SET 
        reviewed = TRUE,
        reviewed_at = CURRENT_TIMESTAMP,
        reviewed_by = reviewer_name,
        action_taken = action_description
    WHERE id = feedback_id;
END;
$$ LANGUAGE plpgsql;

INSERT INTO schema_version (version, description) 
VALUES ('2.1', 'Added conversation feedback system with 3-level rating and suggestions')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- END OF SCHEMA
-- ============================================
