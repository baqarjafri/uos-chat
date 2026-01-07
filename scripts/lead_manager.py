"""
============================================
PROGRESSIVE LEAD CAPTURE SYSTEM
============================================
Purpose: Capture lead data progressively during conversation
Features:
- Name capture at conversation start (hybrid: form or greeting)
- Auto-detect email, phone, country from messages
- Phone country code to country mapping
- Track capture completeness
- Smart escalation asking only for missing fields

Version: 2.0
Created: 2026-01-04
============================================
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from psycopg2.extras import RealDictCursor


@dataclass
class LeadData:
    """Data class for lead information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    country: Optional[str] = None
    nationality: Optional[str] = None
    student_type: Optional[str] = None
    student_level: Optional[str] = None
    programs_interested: List[str] = field(default_factory=list)
    
    # Capture tracking
    capture_source: Dict[str, str] = field(default_factory=dict)
    completeness_score: int = 0
    missing_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "phone_country_code": self.phone_country_code,
            "country": self.country,
            "nationality": self.nationality,
            "student_type": self.student_type,
            "student_level": self.student_level,
            "programs_interested": self.programs_interested,
            "capture_source": self.capture_source,
            "completeness_score": self.completeness_score,
            "missing_fields": self.missing_fields
        }


class LeadManager:
    """
    Manages progressive lead capture throughout conversation.
    Follows ChatGPT-style approach: capture data naturally, ask for missing at end.
    """
    
    # Phone country code patterns (most common first)
    PHONE_PATTERNS = [
        # International format with country code
        r'\+(\d{1,4})[\s.-]?(\d{6,14})',
        # With parentheses
        r'\(?\+(\d{1,4})\)?[\s.-]?(\d{6,14})',
        # Just digits with country code
        r'(\+\d{1,4}\d{6,14})',
    ]
    
    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Name patterns
    NAME_PATTERNS = [
        r"(?:my name is|i'?m|this is|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$",  # Just a name as response
    ]
    
    # Country/nationality patterns
    COUNTRY_PATTERNS = {
        'nigeria': ('Nigeria', 'Nigerian', 'international'),
        'nigerian': ('Nigeria', 'Nigerian', 'international'),
        'india': ('India', 'Indian', 'international'),
        'indian': ('India', 'Indian', 'international'),
        'pakistan': ('Pakistan', 'Pakistani', 'international'),
        'pakistani': ('Pakistan', 'Pakistani', 'international'),
        'china': ('China', 'Chinese', 'international'),
        'chinese': ('China', 'Chinese', 'international'),
        'ghana': ('Ghana', 'Ghanaian', 'international'),
        'ghanaian': ('Ghana', 'Ghanaian', 'international'),
        'kenya': ('Kenya', 'Kenyan', 'international'),
        'kenyan': ('Kenya', 'Kenyan', 'international'),
        'bangladesh': ('Bangladesh', 'Bangladeshi', 'international'),
        'bangladeshi': ('Bangladesh', 'Bangladeshi', 'international'),
        'scotland': ('Scotland', 'Scottish', 'scottish'),
        'scottish': ('Scotland', 'Scottish', 'scottish'),
        'england': ('England', 'English', 'uk'),
        'english': ('England', 'English', 'uk'),
        'wales': ('Wales', 'Welsh', 'uk'),
        'welsh': ('Wales', 'Welsh', 'uk'),
        'northern ireland': ('Northern Ireland', 'Northern Irish', 'uk'),
        'ireland': ('Ireland', 'Irish', 'eu'),
        'irish': ('Ireland', 'Irish', 'eu'),
        'germany': ('Germany', 'German', 'eu'),
        'german': ('Germany', 'German', 'eu'),
        'france': ('France', 'French', 'eu'),
        'french': ('France', 'French', 'eu'),
        'spain': ('Spain', 'Spanish', 'eu'),
        'spanish': ('Spain', 'Spanish', 'eu'),
        'italy': ('Italy', 'Italian', 'eu'),
        'italian': ('Italy', 'Italian', 'eu'),
        'usa': ('United States', 'American', 'international'),
        'america': ('United States', 'American', 'international'),
        'american': ('United States', 'American', 'international'),
        'canada': ('Canada', 'Canadian', 'international'),
        'canadian': ('Canada', 'Canadian', 'international'),
        'australia': ('Australia', 'Australian', 'international'),
        'australian': ('Australia', 'Australian', 'international'),
        'uae': ('United Arab Emirates', 'Emirati', 'international'),
        'dubai': ('United Arab Emirates', 'Emirati', 'international'),
        'saudi': ('Saudi Arabia', 'Saudi', 'international'),
        'qatar': ('Qatar', 'Qatari', 'international'),
    }
    
    def __init__(self, db_connection):
        """Initialize lead manager with database connection"""
        self.conn = db_connection
        self._load_country_codes()
    
    def _load_country_codes(self):
        """Load phone country codes from database"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT country_code, country_name, region FROM phone_country_codes")
            self.country_codes = {
                row['country_code']: {
                    'country': row['country_name'],
                    'region': row['region']
                }
                for row in cursor.fetchall()
            }
        except Exception:
            # Fallback if table doesn't exist
            self.country_codes = {
                '+44': {'country': 'United Kingdom', 'region': 'Europe'},
                '+1': {'country': 'United States/Canada', 'region': 'North America'},
                '+91': {'country': 'India', 'region': 'Asia'},
                '+234': {'country': 'Nigeria', 'region': 'Africa'},
                '+92': {'country': 'Pakistan', 'region': 'Asia'},
            }
    
    def extract_from_message(self, message: str, current_lead: LeadData) -> LeadData:
        """
        Extract lead data from a single message.
        Updates the current lead data with any new information found.
        """
        message_lower = message.lower()
        
        # Extract name
        if not current_lead.name:
            name = self._extract_name(message)
            if name:
                current_lead.name = name
                current_lead.capture_source['name'] = 'conversation'
        
        # Extract email
        if not current_lead.email:
            email = self._extract_email(message)
            if email:
                current_lead.email = email
                current_lead.capture_source['email'] = 'conversation'
        
        # Extract phone and country from phone code
        if not current_lead.phone:
            phone, country_code = self._extract_phone(message)
            if phone:
                current_lead.phone = phone
                current_lead.phone_country_code = country_code
                current_lead.capture_source['phone'] = 'conversation'
                
                # Auto-fill country from phone code
                if country_code and not current_lead.country:
                    country_info = self.country_codes.get(country_code)
                    if country_info:
                        current_lead.country = country_info['country']
                        current_lead.capture_source['country'] = 'phone_code'
        
        # Extract country/nationality from text
        if not current_lead.country or not current_lead.nationality:
            country, nationality, student_type = self._extract_country_nationality(message_lower)
            if country and not current_lead.country:
                current_lead.country = country
                current_lead.capture_source['country'] = 'conversation'
            if nationality and not current_lead.nationality:
                current_lead.nationality = nationality
                current_lead.capture_source['nationality'] = 'conversation'
            if student_type and not current_lead.student_type:
                current_lead.student_type = student_type
        
        # Update completeness
        self._calculate_completeness(current_lead)
        
        return current_lead
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text"""
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Validate it's a reasonable name (not a common word)
                common_words = {'hello', 'hi', 'hey', 'thanks', 'thank', 'please', 'yes', 'no', 'ok', 'okay'}
                if name.lower() not in common_words and len(name) > 1:
                    return name.title()
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        match = re.search(self.EMAIL_PATTERN, text)
        return match.group(0).lower() if match else None
    
    def _extract_phone(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract phone number and country code from text"""
        # Look for phone with country code
        for pattern in self.PHONE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                full_phone = match.group(0)
                # Extract country code
                code_match = re.match(r'\+(\d{1,4})', full_phone)
                if code_match:
                    code = '+' + code_match.group(1)
                    # Try to match to known codes (longest first)
                    for length in [4, 3, 2, 1]:
                        test_code = '+' + code_match.group(1)[:length]
                        if test_code in self.country_codes:
                            return full_phone, test_code
                    return full_phone, code
                return full_phone, None
        return None, None
    
    def _extract_country_nationality(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract country and nationality from text"""
        for keyword, (country, nationality, student_type) in self.COUNTRY_PATTERNS.items():
            if keyword in text:
                return country, nationality, student_type
        return None, None, None
    
    def _calculate_completeness(self, lead: LeadData):
        """Calculate lead completeness score and missing fields"""
        score = 0
        missing = []
        
        # Name: 20 points
        if lead.name:
            score += 20
        else:
            missing.append('name')
        
        # Email: 25 points (most important)
        if lead.email:
            score += 25
        else:
            missing.append('email')
        
        # Phone: 15 points
        if lead.phone:
            score += 15
        else:
            missing.append('phone')
        
        # Country: 10 points
        if lead.country:
            score += 10
        else:
            missing.append('country')
        
        # Program interest: 20 points
        if lead.programs_interested:
            score += 20
        else:
            missing.append('program')
        
        # Study level: 10 points
        if lead.student_level and lead.student_level != 'unknown':
            score += 10
        else:
            missing.append('level')
        
        lead.completeness_score = score
        lead.missing_fields = missing
    
    def generate_greeting_with_name_ask(self, user_name: Optional[str] = None) -> str:
        """Generate greeting that asks for name if not provided"""
        if user_name:
            return f"""Hey {user_name}! 👋 Welcome to the University of Stirling!

I'm here to help with courses, admissions, fees, scholarships - anything you need. What would you like to know?"""
        else:
            return """Hey there! 👋 Welcome to the University of Stirling!

I'm here to help with courses, admissions, fees, scholarships - you name it! Before we dive in, what's your name so I can address you properly?"""
    
    def generate_escalation_prompt(self, lead: LeadData, user_name: Optional[str] = None) -> str:
        """
        Generate escalation prompt asking only for missing fields.
        Includes examples for phone number format.
        """
        name_to_use = user_name or lead.name or "there"
        missing = lead.missing_fields.copy()
        
        # Remove fields we already have
        if lead.name:
            missing = [f for f in missing if f != 'name']
        if lead.email:
            missing = [f for f in missing if f != 'email']
        if lead.phone:
            missing = [f for f in missing if f != 'phone']
        
        # Build the prompt based on what's missing
        if not missing or (len(missing) == 1 and missing[0] in ['program', 'level', 'country']):
            # We have enough for escalation
            if lead.email:
                return None  # No need to ask, we have email
        
        prompt_parts = [f"Thanks {name_to_use}! I'd love to connect you with our admissions team for a detailed response."]
        
        ask_items = []
        
        if 'name' in missing:
            ask_items.append("**Your name**")
        
        if 'email' in missing:
            ask_items.append("**Your email address**")
        
        if 'phone' in missing:
            ask_items.append("**Your phone number** (with country code, e.g., +44 7911 123456 for UK, +234 801 234 5678 for Nigeria, +91 98765 43210 for India)")
        
        if ask_items:
            prompt_parts.append("\nCould you please share:")
            for item in ask_items:
                prompt_parts.append(f"- {item}")
            prompt_parts.append("\nOur team will review your query and get back to you within 1-2 business days.")
        
        return "\n".join(prompt_parts)
    
    def save_lead_to_db(
        self,
        conversation_id: int,
        lead: LeadData,
        user_query: str,
        conversation_summary: str,
        escalation_reason: str,
        last_messages: List[Dict]
    ) -> int:
        """Save lead to database with full context"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO leads (
                conversation_id, name, email, phone, phone_country_code,
                location, country, nationality, student_type, student_level,
                programs_interested, capture_source,
                user_query, conversation_summary, escalation_reason, last_messages
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            conversation_id,
            lead.name or "Unknown",
            lead.email,
            lead.phone,
            lead.phone_country_code,
            lead.country,  # location
            lead.country,
            lead.nationality,
            lead.student_type,
            lead.student_level,
            lead.programs_interested,
            json.dumps(lead.capture_source),
            user_query,
            conversation_summary,
            escalation_reason,
            json.dumps(last_messages)
        ))
        
        lead_id = cursor.fetchone()[0]
        
        # Update conversation
        cursor.execute("""
            UPDATE conversations
            SET lead_captured = TRUE, 
                lead_id = %s,
                user_name = %s,
                nationality = %s,
                lead_data = %s,
                lead_capture_completeness = %s
            WHERE id = %s
        """, (
            lead_id,
            lead.name,
            lead.nationality,
            json.dumps(lead.to_dict()),
            lead.completeness_score,
            conversation_id
        ))
        
        self.conn.commit()
        return lead_id
    
    def update_conversation_lead_data(
        self,
        conversation_id: int,
        lead: LeadData
    ):
        """Update conversation with progressive lead data"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE conversations
            SET user_name = COALESCE(%s, user_name),
                nationality = COALESCE(%s, nationality),
                lead_data = %s,
                lead_capture_completeness = %s
            WHERE id = %s
        """, (
            lead.name,
            lead.nationality,
            json.dumps(lead.to_dict()),
            lead.completeness_score,
            conversation_id
        ))
        
        self.conn.commit()
    
    def get_lead_from_conversation(self, conversation_id: int) -> LeadData:
        """Load existing lead data from conversation"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT user_name, nationality, detected_location, student_type, 
                   student_level, programs_discussed, lead_data
            FROM conversations
            WHERE id = %s
        """, (conversation_id,))
        
        row = cursor.fetchone()
        if not row:
            return LeadData()
        
        lead = LeadData(
            name=row['user_name'],
            nationality=row['nationality'],
            country=row['detected_location'],
            student_type=row['student_type'],
            student_level=row['student_level'],
            programs_interested=row['programs_discussed'] or []
        )
        
        # Merge with stored lead_data if exists
        if row['lead_data']:
            stored = row['lead_data'] if isinstance(row['lead_data'], dict) else {}
            lead.email = stored.get('email')
            lead.phone = stored.get('phone')
            lead.phone_country_code = stored.get('phone_country_code')
            lead.capture_source = stored.get('capture_source', {})
        
        self._calculate_completeness(lead)
        return lead


# ============================================
# HELPER FUNCTIONS
# ============================================

def should_ask_for_name(conversation_history: List[Dict], name_asked: bool) -> bool:
    """Determine if we should ask for the user's name"""
    # Don't ask if we already asked
    if name_asked:
        return False
    
    # Ask on first message (greeting)
    if len(conversation_history) == 0:
        return True
    
    return False


def personalize_response(response: str, user_name: Optional[str]) -> str:
    """Add personalization to response if we have user's name"""
    if not user_name:
        return response
    
    # Add name to greeting-style responses
    greetings = ['great question', 'good question', 'absolutely', 'sure thing', 'of course']
    for greeting in greetings:
        if response.lower().startswith(greeting):
            return f"{user_name}, {response}"
    
    return response
