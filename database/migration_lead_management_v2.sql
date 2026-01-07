-- ============================================
-- LEAD MANAGEMENT SYSTEM V2 - MIGRATION SCRIPT
-- ============================================
-- Purpose: Add progressive lead capture with personalization
-- Version: 2.2
-- Created: 2026-01-04
-- 
-- Changes:
-- 1. Add user_name to conversations for early personalization
-- 2. Add nationality field separate from location
-- 3. Add phone_country_code for automatic country detection
-- 4. Add lead_data JSONB for progressive capture tracking
-- 5. Add capture_completeness score
-- ============================================

-- ============================================
-- 1. EXTEND CONVERSATIONS TABLE
-- ============================================
-- Add user_name for personalization (captured at start)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_name VARCHAR(100);

-- Add nationality (separate from location - e.g., Nigerian living in UK)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS nationality VARCHAR(100);

-- Add progressive lead data (stores partial info as JSON)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS lead_data JSONB DEFAULT '{}';

-- Add capture completeness percentage (0-100)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS lead_capture_completeness INTEGER DEFAULT 0;

-- Add name_asked flag to avoid asking twice
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS name_asked BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN conversations.user_name IS 'User first name for personalization, captured at conversation start';
COMMENT ON COLUMN conversations.nationality IS 'User nationality (can differ from current location)';
COMMENT ON COLUMN conversations.lead_data IS 'Progressive lead capture data as JSON';
COMMENT ON COLUMN conversations.lead_capture_completeness IS 'Percentage of lead data captured (0-100)';
COMMENT ON COLUMN conversations.name_asked IS 'Whether we have asked for the users name';

-- ============================================
-- 2. EXTEND LEADS TABLE
-- ============================================
-- Add phone_country_code for automatic country detection
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS phone_country_code VARCHAR(10);

-- Add nationality (separate from location)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS nationality VARCHAR(100);

-- Add country (auto-filled from phone country code)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS country VARCHAR(100);

-- Add capture_source to track how each field was captured
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS capture_source JSONB DEFAULT '{}';

-- Add user_query and conversation_summary for context
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS user_query TEXT;

ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS conversation_summary TEXT;

-- Add escalation_reason
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS escalation_reason TEXT;

-- Add last_messages for context
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS last_messages JSONB;

COMMENT ON COLUMN leads.phone_country_code IS 'Phone country code (e.g., +44, +234)';
COMMENT ON COLUMN leads.nationality IS 'User nationality';
COMMENT ON COLUMN leads.country IS 'Country auto-filled from phone country code';
COMMENT ON COLUMN leads.capture_source IS 'How each field was captured: form, conversation, escalation';

-- ============================================
-- 3. PHONE COUNTRY CODE TO COUNTRY MAPPING TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS phone_country_codes (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) NOT NULL UNIQUE,
    country_name VARCHAR(100) NOT NULL,
    country_iso VARCHAR(3),
    region VARCHAR(50)
);

-- Insert common country codes (focus on Stirling's target markets)
INSERT INTO phone_country_codes (country_code, country_name, country_iso, region) VALUES
-- UK & Ireland
('+44', 'United Kingdom', 'GBR', 'Europe'),
('+353', 'Ireland', 'IRL', 'Europe'),

-- Europe
('+33', 'France', 'FRA', 'Europe'),
('+49', 'Germany', 'DEU', 'Europe'),
('+34', 'Spain', 'ESP', 'Europe'),
('+39', 'Italy', 'ITA', 'Europe'),
('+31', 'Netherlands', 'NLD', 'Europe'),
('+32', 'Belgium', 'BEL', 'Europe'),
('+41', 'Switzerland', 'CHE', 'Europe'),
('+43', 'Austria', 'AUT', 'Europe'),
('+45', 'Denmark', 'DNK', 'Europe'),
('+46', 'Sweden', 'SWE', 'Europe'),
('+47', 'Norway', 'NOR', 'Europe'),
('+48', 'Poland', 'POL', 'Europe'),
('+351', 'Portugal', 'PRT', 'Europe'),
('+30', 'Greece', 'GRC', 'Europe'),

-- Africa (key markets)
('+234', 'Nigeria', 'NGA', 'Africa'),
('+233', 'Ghana', 'GHA', 'Africa'),
('+254', 'Kenya', 'KEN', 'Africa'),
('+27', 'South Africa', 'ZAF', 'Africa'),
('+20', 'Egypt', 'EGY', 'Africa'),
('+212', 'Morocco', 'MAR', 'Africa'),
('+263', 'Zimbabwe', 'ZWE', 'Africa'),
('+256', 'Uganda', 'UGA', 'Africa'),
('+255', 'Tanzania', 'TZA', 'Africa'),
('+237', 'Cameroon', 'CMR', 'Africa'),

-- Asia (key markets)
('+91', 'India', 'IND', 'Asia'),
('+92', 'Pakistan', 'PAK', 'Asia'),
('+86', 'China', 'CHN', 'Asia'),
('+81', 'Japan', 'JPN', 'Asia'),
('+82', 'South Korea', 'KOR', 'Asia'),
('+65', 'Singapore', 'SGP', 'Asia'),
('+60', 'Malaysia', 'MYS', 'Asia'),
('+66', 'Thailand', 'THA', 'Asia'),
('+84', 'Vietnam', 'VNM', 'Asia'),
('+62', 'Indonesia', 'IDN', 'Asia'),
('+63', 'Philippines', 'PHL', 'Asia'),
('+880', 'Bangladesh', 'BGD', 'Asia'),
('+94', 'Sri Lanka', 'LKA', 'Asia'),
('+977', 'Nepal', 'NPL', 'Asia'),

-- Middle East
('+971', 'United Arab Emirates', 'ARE', 'Middle East'),
('+966', 'Saudi Arabia', 'SAU', 'Middle East'),
('+974', 'Qatar', 'QAT', 'Middle East'),
('+973', 'Bahrain', 'BHR', 'Middle East'),
('+968', 'Oman', 'OMN', 'Middle East'),
('+965', 'Kuwait', 'KWT', 'Middle East'),
('+962', 'Jordan', 'JOR', 'Middle East'),
('+961', 'Lebanon', 'LBN', 'Middle East'),
('+90', 'Turkey', 'TUR', 'Middle East'),

-- Americas
('+1', 'United States/Canada', 'USA', 'North America'),
('+52', 'Mexico', 'MEX', 'North America'),
('+55', 'Brazil', 'BRA', 'South America'),
('+54', 'Argentina', 'ARG', 'South America'),
('+57', 'Colombia', 'COL', 'South America'),
('+56', 'Chile', 'CHL', 'South America'),

-- Oceania
('+61', 'Australia', 'AUS', 'Oceania'),
('+64', 'New Zealand', 'NZL', 'Oceania')

ON CONFLICT (country_code) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_phone_country_codes_code ON phone_country_codes(country_code);

-- ============================================
-- 4. LEAD CAPTURE TRACKING TABLE
-- ============================================
-- Tracks what lead fields have been captured and how
CREATE TABLE IF NOT EXISTS lead_capture_tracking (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Field tracking (when and how each field was captured)
    name_captured_at TIMESTAMP,
    name_source VARCHAR(50), -- 'form', 'greeting', 'conversation', 'escalation'
    
    email_captured_at TIMESTAMP,
    email_source VARCHAR(50),
    
    phone_captured_at TIMESTAMP,
    phone_source VARCHAR(50),
    
    country_captured_at TIMESTAMP,
    country_source VARCHAR(50), -- 'phone_code', 'conversation', 'form'
    
    program_captured_at TIMESTAMP,
    program_source VARCHAR(50),
    
    level_captured_at TIMESTAMP,
    level_source VARCHAR(50),
    
    -- Missing fields tracking
    missing_fields TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(conversation_id)
);

CREATE INDEX IF NOT EXISTS idx_lead_capture_tracking_conversation ON lead_capture_tracking(conversation_id);

COMMENT ON TABLE lead_capture_tracking IS 'Tracks progressive lead capture - what fields captured and how';

-- ============================================
-- 5. HELPER FUNCTION: Get Country from Phone Code
-- ============================================
CREATE OR REPLACE FUNCTION get_country_from_phone(phone_number VARCHAR)
RETURNS TABLE (
    country_code VARCHAR,
    country_name VARCHAR,
    country_iso VARCHAR,
    region VARCHAR
) AS $$
DECLARE
    extracted_code VARCHAR;
BEGIN
    -- Extract country code from phone number (handles +XX, +XXX, +XXXX formats)
    -- Try longest codes first (4 digits like +1242), then 3, then 2
    
    -- Try 4-digit codes
    extracted_code := substring(phone_number from '^\+(\d{4})');
    IF extracted_code IS NOT NULL THEN
        RETURN QUERY SELECT p.country_code, p.country_name, p.country_iso, p.region
        FROM phone_country_codes p WHERE p.country_code = '+' || extracted_code;
        IF FOUND THEN RETURN; END IF;
    END IF;
    
    -- Try 3-digit codes
    extracted_code := substring(phone_number from '^\+(\d{3})');
    IF extracted_code IS NOT NULL THEN
        RETURN QUERY SELECT p.country_code, p.country_name, p.country_iso, p.region
        FROM phone_country_codes p WHERE p.country_code = '+' || extracted_code;
        IF FOUND THEN RETURN; END IF;
    END IF;
    
    -- Try 2-digit codes
    extracted_code := substring(phone_number from '^\+(\d{2})');
    IF extracted_code IS NOT NULL THEN
        RETURN QUERY SELECT p.country_code, p.country_name, p.country_iso, p.region
        FROM phone_country_codes p WHERE p.country_code = '+' || extracted_code;
        IF FOUND THEN RETURN; END IF;
    END IF;
    
    -- Try 1-digit code (+1 for US/Canada)
    extracted_code := substring(phone_number from '^\+(\d{1})');
    IF extracted_code IS NOT NULL THEN
        RETURN QUERY SELECT p.country_code, p.country_name, p.country_iso, p.region
        FROM phone_country_codes p WHERE p.country_code = '+' || extracted_code;
    END IF;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. HELPER FUNCTION: Calculate Lead Completeness
-- ============================================
CREATE OR REPLACE FUNCTION calculate_lead_completeness(
    p_name VARCHAR,
    p_email VARCHAR,
    p_phone VARCHAR,
    p_country VARCHAR,
    p_program TEXT[],
    p_level VARCHAR
)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
    max_score INTEGER := 100;
BEGIN
    -- Name: 20 points
    IF p_name IS NOT NULL AND p_name != '' THEN
        score := score + 20;
    END IF;
    
    -- Email: 25 points (most important for follow-up)
    IF p_email IS NOT NULL AND p_email != '' THEN
        score := score + 25;
    END IF;
    
    -- Phone: 15 points
    IF p_phone IS NOT NULL AND p_phone != '' THEN
        score := score + 15;
    END IF;
    
    -- Country: 10 points
    IF p_country IS NOT NULL AND p_country != '' THEN
        score := score + 10;
    END IF;
    
    -- Program interest: 20 points
    IF p_program IS NOT NULL AND array_length(p_program, 1) > 0 THEN
        score := score + 20;
    END IF;
    
    -- Study level: 10 points
    IF p_level IS NOT NULL AND p_level != '' AND p_level != 'unknown' THEN
        score := score + 10;
    END IF;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. TRIGGER: Auto-update lead completeness
-- ============================================
CREATE OR REPLACE FUNCTION update_lead_completeness()
RETURNS TRIGGER AS $$
BEGIN
    NEW.lead_capture_completeness := calculate_lead_completeness(
        NEW.user_name,
        (NEW.lead_data->>'email')::VARCHAR,
        (NEW.lead_data->>'phone')::VARCHAR,
        COALESCE(NEW.nationality, NEW.detected_location),
        NEW.programs_discussed,
        NEW.student_level
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS trigger_update_lead_completeness ON conversations;
CREATE TRIGGER trigger_update_lead_completeness
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_lead_completeness();

-- ============================================
-- 8. VIEW: Lead Capture Progress
-- ============================================
CREATE OR REPLACE VIEW lead_capture_progress AS
SELECT 
    c.id as conversation_id,
    c.session_id,
    c.user_name,
    c.lead_capture_completeness,
    c.lead_captured,
    c.student_type,
    c.student_level,
    c.nationality,
    c.detected_location,
    c.programs_discussed,
    c.lead_data,
    c.created_at,
    -- What's missing
    CASE WHEN c.user_name IS NULL OR c.user_name = '' THEN 'name' END as missing_name,
    CASE WHEN c.lead_data->>'email' IS NULL THEN 'email' END as missing_email,
    CASE WHEN c.lead_data->>'phone' IS NULL THEN 'phone' END as missing_phone,
    CASE WHEN c.nationality IS NULL AND c.detected_location IS NULL THEN 'country' END as missing_country,
    CASE WHEN c.programs_discussed IS NULL OR array_length(c.programs_discussed, 1) IS NULL THEN 'program' END as missing_program,
    CASE WHEN c.student_level IS NULL OR c.student_level = 'unknown' THEN 'level' END as missing_level
FROM conversations c
ORDER BY c.created_at DESC;

-- ============================================
-- 9. UPDATE SCHEMA VERSION
-- ============================================
INSERT INTO schema_version (version, description) 
VALUES ('2.2', 'Added progressive lead capture with personalization, phone country code mapping, and lead completeness tracking')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- END OF MIGRATION
-- ============================================
