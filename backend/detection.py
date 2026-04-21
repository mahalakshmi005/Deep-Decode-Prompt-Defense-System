import re
import torch
import base64
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class DetectionEngine:
    def __init__(self, model_name="ProtectAI/deberta-v3-base-prompt-injection-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

        # Suspicious patterns for rule-based detection
        self.rules = [
            r"(?i)ignore\s+(all\s+)?previous\s+instructions",
            r"(?i)system\s+prompt",
            r"(?i)you\s+are\s+now\s+a\s+DAN",
            r"(?i)stay\s+in\s+character",
            r"(?i)bypass\s+filter",
            r"(?i)jailbreak",
            r"(?i)override\s+security",
            r"(?i)forget\s+everything\s+you\s+know",
            r"(?i)respond\s+as\s+if\s+you\s+were",
            r"(?i)do\s+not\s+mention\s+safety",
            # Added patterns for hacking and manipulation
            r"(?i)enter\s+into\s+system",
            r"(?i)remote\s+server",
            r"(?i)hack(ing)?",
            r"(?i)exploit",
            r"(?i)vulnerability",
            r"(?i)bypass",
            r"(?i)steal",
            r"(?i)malicious",
            r"(?i)reverse\s+shell",
            r"(?i)privilege\s+escalation",
            r"(?i)backdoor",
            r"(?i)unauthorized",

        ]

    def _extract_and_decode_base64(self, text: str) -> list:
        """Finds potential base64 strings and decodes them."""
        # This regex looks for base64-like strings (length > 8 to avoid noise)
        base64_pattern = r'[A-Za-z0-9+/]{8,}(?:={0,2})'
        potential_matches = re.findall(base64_pattern, text)
        
        decoded_contents = []
        for match in potential_matches:
            try:
                # Add padding if necessary
                padded_match = match + "=" * ((4 - len(match) % 4) % 4)
                decoded = base64.b64decode(padded_match).decode('utf-8', errors='ignore')
                # Only keep it if it looks like actual text (has spaces/common words)
                if len(decoded.strip()) > 3:
                    decoded_contents.append(decoded)
            except Exception:
                continue
        return decoded_contents

    def rule_based_score(self, text: str) -> float:
        """Calculates a risk score based on regex rules (0-100)."""
        matches = 0
        for rule in self.rules:
            if re.search(rule, text):
                matches += 1
        
        # Simple scoring: 35 per match, capped at 100
        score = min(matches * 35, 100)
        return float(score)

    def ml_based_score(self, text: str) -> dict:
        """Calculates a risk score using the ML model."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            injection_prob = probabilities[0][1].item()
            
        return {
            "score": injection_prob * 100,
            "classification": "INJECTION" if injection_prob > 0.5 else "SAFE"
        }

    def get_combined_score(self, text: str) -> dict:
        """Combines rule-based, ML, and Base64-decoded scores."""
        # 1. Analyze original text
        rule_score = self.rule_based_score(text)
        ml_data = self.ml_based_score(text)
        ml_score = ml_data["score"]
        
        # 2. Analyze Base64 decoded content
        decoded_texts = self._extract_and_decode_base64(text)
        decoded_rule_scores = [self.rule_based_score(dt) for dt in decoded_texts]
        decoded_ml_scores = [self.ml_based_score(dt)["score"] for dt in decoded_texts]
        
        # Combine all findings
        max_rule_score = max([rule_score] + decoded_rule_scores)
        max_ml_score = max([ml_score] + decoded_ml_scores)
        
        combined_score = max(max_rule_score, max_ml_score)
        
        if combined_score < 30:
            classification = "SAFE"
        elif combined_score < 70:
            classification = "WARNING"
        else:
            classification = "BLOCK"
            
        return {
            "score": combined_score,
            "classification": classification,
            "rule_score": max_rule_score,
            "ml_score": max_ml_score,
            "base64_detected": len(decoded_texts) > 0,
            "decoded_content": decoded_texts if decoded_texts else None
        }
