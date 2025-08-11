"""
AI Safety Module for Ollama Integration
Implements content filtering, prompt sanitization, and safety guardrails
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AISafetyGuard:
    """AI Safety guardrails for Ollama interactions"""
    
    def __init__(self):
        self.blocked_patterns = self._load_blocked_patterns()
        self.request_history = []
        self.max_requests_per_minute = 10
        self.max_query_length = 2000
        
    def _load_blocked_patterns(self) -> List[str]:
        """Load patterns that should be blocked for safety"""
        return [
            # Malicious patterns
            r'(?i)hack|exploit|vulnerability|backdoor|malware',
            r'(?i)bypass.*security|override.*safety|disable.*filter',
            r'(?i)jailbreak|prompt.*injection|ignore.*instructions',
            
            # Financial manipulation
            r'(?i)pump.*dump|market.*manipulation|insider.*trading',
            r'(?i)fake.*price|manipulate.*market|artificial.*inflation',
            
            # Personal data requests
            r'(?i)private.*key|wallet.*seed|password|personal.*data',
            r'(?i)social.*security|credit.*card|bank.*account',
            
            # Harmful content
            r'(?i)illegal.*activity|money.*laundering|tax.*evasion',
            r'(?i)terrorist.*financing|sanctions.*evasion',
            
            # System manipulation
            r'(?i)system.*prompt|role.*play.*as|pretend.*to.*be',
            r'(?i)act.*as.*if|simulate.*being|become.*character',
        ]
    
    def sanitize_query(self, query: str) -> Tuple[str, bool, str]:
        """
        Sanitize user query for safety
        Returns: (sanitized_query, is_safe, reason)
        """
        if not query or not query.strip():
            return "", False, "Empty query"
        
        # Check query length
        if len(query) > self.max_query_length:
            return "", False, f"Query too long ({len(query)} chars, max {self.max_query_length})"
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, query):
                logger.warning(f"Blocked unsafe query pattern: {pattern}")
                return "", False, "Query contains potentially unsafe content"
        
        # Basic sanitization
        sanitized = query.strip()
        sanitized = re.sub(r'[<>]', '', sanitized)  # Remove HTML brackets
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalize whitespace
        
        return sanitized, True, "Query is safe"
    
    def check_rate_limit(self, user_id: str = "default") -> Tuple[bool, str]:
        """Check if request rate limit is exceeded"""
        current_time = datetime.now()
        
        # Clean old requests (older than 1 minute)
        self.request_history = [
            req for req in self.request_history 
            if current_time - req['timestamp'] < timedelta(minutes=1)
        ]
        
        # Count requests from this user in the last minute
        user_requests = [
            req for req in self.request_history 
            if req['user_id'] == user_id
        ]
        
        if len(user_requests) >= self.max_requests_per_minute:
            return False, f"Rate limit exceeded: {len(user_requests)}/{self.max_requests_per_minute} requests per minute"
        
        # Add current request
        self.request_history.append({
            'user_id': user_id,
            'timestamp': current_time
        })
        
        return True, "Rate limit OK"
    
    def validate_ollama_response(self, response: str) -> Tuple[str, bool, str]:
        """
        Validate Ollama response for safety and quality
        Returns: (cleaned_response, is_valid, reason)
        """
        if not response or not response.strip():
            return "", False, "Empty response from Ollama"
        
        # Check for dangerous content in response
        dangerous_patterns = [
            r'(?i)here.*is.*how.*to.*hack',
            r'(?i)steps.*to.*exploit',
            r'(?i)bypass.*security.*by',
            r'(?i)manipulate.*market.*by',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, response):
                logger.warning(f"Blocked unsafe Ollama response: {pattern}")
                return "", False, "Response contains potentially unsafe content"
        
        # Basic response cleaning
        cleaned = response.strip()
        
        # Remove any potential HTML/JavaScript
        cleaned = re.sub(r'<script.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Ensure response is within reasonable length
        if len(cleaned) > 10000:  # 10k character limit
            cleaned = cleaned[:10000] + "\n\n[Response truncated for safety]"
        
        return cleaned, True, "Response is safe"
    
    def validate_gemini_response(self, response: str) -> Tuple[str, bool, str]:
        """
        Validate Gemini response for safety and quality
        Returns: (cleaned_response, is_valid, reason)
        """
        if not response or not response.strip():
            return "", False, "Empty response from Gemini"
        
        # Check for dangerous content in response
        dangerous_patterns = [
            r'(?i)here.*is.*how.*to.*hack',
            r'(?i)steps.*to.*exploit',
            r'(?i)bypass.*security.*by',
            r'(?i)manipulate.*market.*by',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, response):
                logger.warning(f"Blocked unsafe Gemini response: {pattern}")
                return "", False, "Response contains potentially unsafe content"
        
        # Basic response cleaning
        cleaned = response.strip()
        
        # Remove any potential HTML/JavaScript
        cleaned = re.sub(r'<script.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Ensure response is within reasonable length
        if len(cleaned) > 10000:  # 10k character limit
            cleaned = cleaned[:10000] + "\n\n[Response truncated for safety]"
        
        return cleaned, True, "Response is safe"
    
    def create_safe_prompt(self, user_query: str, tool_context: str) -> str:
        """Create a safety-enhanced prompt for Ollama"""
        safety_instructions = """
SAFETY GUIDELINES:
- Provide only factual, helpful information about cryptocurrency and blockchain
- Do not provide advice on market manipulation, illegal activities, or harmful content
- Focus on educational and analytical content
- If asked about unsafe topics, politely decline and redirect to safe alternatives
- Base your response strictly on the provided data

"""
        
        prompt = f"""{safety_instructions}

USER QUERY: {user_query}

CONTEXT DATA:
{tool_context}

INSTRUCTIONS:
- Answer the user's cryptocurrency question using only the provided context data
- Be professional, accurate, and helpful
- If the data doesn't support a complete answer, acknowledge the limitations
- Provide educational insights where appropriate
- Keep responses focused on legitimate cryptocurrency analysis

RESPONSE:"""
        
        return prompt
    
    def log_safety_event(self, event_type: str, details: Dict[str, Any]):
        """Log safety-related events for monitoring"""
        logger.info(f"AI Safety Event: {event_type} - {details}")

# Global safety instance
ai_safety = AISafetyGuard()
