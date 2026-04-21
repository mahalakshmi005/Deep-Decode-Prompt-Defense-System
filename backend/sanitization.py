import re

class SanitizationEngine:
    def __init__(self):
        # Patterns to neutralize
        self.neutralize_patterns = [
            (r"(?i)ignore\s+(all\s+)?previous\s+instructions", "[SECURE_REMOVED: instruction override attempt]"),
            (r"(?i)system\s+prompt", "[SECURE_REMOVED: system prompt reference]"),
            (r"(?i)you\s+are\s+now\s+a\s+DAN", "[SECURE_REMOVED: roleplay attempt]"),
            (r"(?i)jailbreak", "[SECURE_REMOVED: jailbreak term]"),
        ]

    def sanitize(self, text: str) -> str:
        """Cleans or neutralizes unsafe or adversarial instructions."""
        sanitized_text = text
        for pattern, replacement in self.neutralize_patterns:
            sanitized_text = re.sub(pattern, replacement, sanitized_text)
        
        # Additionally, trim excessive spaces which are sometimes used for obfuscation
        sanitized_text = re.sub(r"\s+", " ", sanitized_text).strip()
        
        return sanitized_text
