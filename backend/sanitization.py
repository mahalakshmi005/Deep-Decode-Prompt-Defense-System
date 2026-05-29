import re
from obfuscation import ObfuscationEngine

class SanitizationEngine:
    def __init__(self):
        self.obfuscation_engine = ObfuscationEngine()
        # Patterns that indicate an injection attempt or instruction override
        # These will be used to split the prompt and discard everything after the trigger
        self.injection_split_patterns = [
            r"(?i)\[\s*ignore\s+(all\s+)?previous\s+instruction(s)?\s*\]",
            r"(?i)ignore\s+(all\s+)?previous\s+instruction(s)?",
            r"(?i)\[\s*ignore\s+previous\s*\]",
            r"(?i)system\s+prompt",
            r"(?i)you\s+are\s+now\s+a\s+DAN",
            r"(?i)stay\s+in\s+character",
            r"(?i)jailbreak",
        ]
        
        # Patterns for neutral replacement if we can't cleanly split but want to neutralize keywords
        self.neutralize_patterns = [
            (r"(?i)how\s+to\s+hack\s+a\s+website", "[SECURE_REMOVED: hacking request]"),
            (r"(?i)generate\s+malware", "[SECURE_REMOVED: malware request]"),
        ]

    def redact_pii(self, text: str) -> str:
        """Redacts sensitive information like emails and phone numbers (OWASP LLM06)."""
        text, _ = self.detect_and_redact_pii(text)
        return text

    def detect_and_redact_pii(self, text: str) -> tuple:
        """Redacts PII and returns the redacted text along with a list of PII types found."""
        pii_found = []
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, text):
            pii_found.append("Email")
        text = re.sub(email_pattern, "[REDACTED_EMAIL]", text)
        
        # Simple phone pattern
        phone_pattern = r'\b\d{10}\b|\+\d{1,3}\s?\d{10}'
        if re.search(phone_pattern, text):
            pii_found.append("Phone Number")
        text = re.sub(phone_pattern, "[REDACTED_PHONE]", text)
        
        return text, pii_found

    def sanitize(self, text: str) -> str:
        """Cleans or neutralizes unsafe or adversarial instructions."""
        # First, unmask obfuscation
        clean_text = self.obfuscation_engine.get_clean_text(text)
        
        # New: Redact PII before processing (OWASP LLM06)
        clean_text = self.redact_pii(clean_text)
        
        # Split the text. If an injection pattern is found, we only keep what's BEFORE it.
        earliest_match_pos = len(clean_text)
        found_any = False
        
        for pattern in self.injection_split_patterns:
            match = re.search(pattern, clean_text)
            if match:
                if match.start() < earliest_match_pos:
                    earliest_match_pos = match.start()
                    found_any = True
        
        if found_any:
            # Keep only the safe part before the injection
            sanitized_text = clean_text[:earliest_match_pos].strip()
        else:
            sanitized_text = clean_text
            
        # Apply additional neutralization for specific harmful keywords
        for pattern, replacement in self.neutralize_patterns:
            sanitized_text = re.sub(pattern, replacement, sanitized_text)
        
        # Final cleanup: trim excessive spaces
        sanitized_text = re.sub(r"\s+", " ", sanitized_text).strip()
        
        # If we removed everything, return a safe notice
        if not sanitized_text:
            return "Note: Malicious instruction blocked. Please provide a safe request."
            
        return sanitized_text
