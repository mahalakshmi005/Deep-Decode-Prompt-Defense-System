import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from obfuscation import ObfuscationEngine

class DetectionEngine:
    def __init__(self, model_name="ProtectAI/deberta-v3-base-prompt-injection-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        self.obfuscation_engine = ObfuscationEngine()

        # Core Global Rules
        self.base_rules = [
            r"(?i)ignore\s+(all\s+)?previous\s+instruction(s)?",
            r"(?i)\[\s*ignore\s+previous\s*\]",
            r"(?i)ignore\s+previous",
            r"(?i)system\s+prompt",
            r"(?i)jailbreak",
        ]

        # Context-Specific Rule Sets
        self.context_rules = {
            "HARMFUL": [
                r"(?i)how\s+to\s+(make|create|build|construct)\s+a?\s*bomb",
                r"(?i)create\s+(explosive|weapon)",
                r"(?i)illegal\s+drug",
                r"(?i)methamphetamine",
                r"(?i)hack\s+into",
                r"(?i)steal\s+credit\s+card",
                r"(?i)generate\s+malware"
            ],
            "ROLEPLAY": [
                r"(?i)you\s+are\s+now\s+a\s+DAN",
                r"(?i)stay\s+in\s+character",
                r"(?i)respond\s+as\s+if\s+you\s+were",
                r"(?i)no\s+restrictions",
                r"(?i)unfiltered"
            ],
            "SYSTEM": [
                r"(?i)override\s+security",
                r"(?i)forget\s+everything",
                r"(?i)root\s+access",
                r"(?i)developer\s+mode",
                r"(?i)admin\s+privileges"
            ],
            "HACKING": [
                r"(?i)remote\s+server",
                r"(?i)exploit",
                r"(?i)vulnerability",
                r"(?i)reverse\s+shell",
                r"(?i)backdoor",
                r"(?i)unauthorized"
            ],
            "DATA_EXFIL": [
                r"(?i)list\s+all\s+files",
                r"(?i)dump\s+database",
                r"(?i)export\s+secrets",
                r"(?i)api\s+keys"
            ]
        }

    def _detect_context(self, text: str) -> list:
        """Identifies the context of the prompt to select relevant rules."""
        contexts = []
        text = text.lower()
        
        if any(w in text for w in ["act", "character", "pretend", "roleplay", "persona"]):
            contexts.append("ROLEPLAY")
        if any(w in text for w in ["system", "bios", "kernel", "admin", "config", "setting"]):
            contexts.append("SYSTEM")
        if any(w in text for w in ["hack", "exploit", "bypass", "security", "vuln"]):
            contexts.append("HACKING")
        if any(w in text for w in ["data", "db", "database", "extract", "download", "keys"]):
            contexts.append("DATA_EXFIL")
        if any(w in text for w in ["bomb", "explosive", "illegal", "drug", "steal", "malware", "hack"]):
            contexts.append("HARMFUL")
            
        return contexts

    def rule_based_score(self, text: str, contexts: list) -> dict:
        """Calculates risk score using base rules and context-specific rules."""
        matches = []
        base_match = False
        harmful_match = False
        
        # Check Base Rules
        for rule in self.base_rules:
            if re.search(rule, text):
                matches.append(rule)
                base_match = True
        
        # Check Context-Specific Rules
        for ctx in contexts:
            for rule in self.context_rules.get(ctx, []):
                if re.search(rule, text):
                    matches.append(f"[{ctx}] {rule}")
                    if ctx == "HARMFUL":
                        harmful_match = True
        
        # If a base rule matches, the score starts at 40% (WARNING)
        # If a harmful rule matches, it starts at 80% (BLOCK)
        score = 0
        if harmful_match:
            score = 80 + (len(matches) - 1) * 10
        elif base_match:
            score = 40 + (len(matches) - 1) * 20
        else:
            score = len(matches) * 30
            
        score = min(score, 100)
        return {"score": float(score), "patterns_found": matches}

    def ml_based_score(self, text: str) -> dict:
        """Calculates a risk score using the ML model with confidence estimation."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            injection_prob = probabilities[0][1].item()
            
        # Confidence is higher the further we are from 0.5 (the point of maximum uncertainty)
        # We normalize this to a 0-100 scale
        confidence_score = abs(injection_prob - 0.5) * 200
        
        confidence_level = "LOW"
        if confidence_score > 80: confidence_level = "HIGH"
        elif confidence_score > 40: confidence_level = "MEDIUM"

        return {
            "score": injection_prob * 100,
            "confidence_score": round(confidence_score, 2),
            "confidence_level": confidence_level,
            "classification": "INJECTION" if injection_prob > 0.5 else "SAFE"
        }

    def get_combined_score(self, text: str) -> dict:
        """Combines context-aware rules, ML, and deobfuscation."""
        # 1. Context Detection
        contexts = self._detect_context(text)
        
        # 2. Rule-based analysis (Contextual)
        rule_data = self.rule_based_score(text, contexts)
        
        # 3. ML Analysis
        ml_data = self.ml_based_score(text)
        
        # 4. Obfuscation check (Normalized & Decoded)
        clean_text = self.obfuscation_engine.get_clean_text(text)
        clean_rule_data = self.rule_based_score(clean_text, contexts) if clean_text != text else {"score": 0, "patterns_found": []}
        
        decoded_texts = self.obfuscation_engine.extract_and_decode_all(text)
        max_decoded_rule_score = 0
        if decoded_texts:
            max_decoded_rule_score = max([self.rule_based_score(dt, contexts)["score"] for dt in decoded_texts])
        
        # Final Synthesis
        # If the injection is hidden in decoded text, we treat it as a deliberate attack (BLOCK)
        final_rule_score = max(rule_data["score"], clean_rule_data["score"])
        
        # Special check for common injection keywords even if not part of a full sentence
        # if they were obfuscated
        # Only flag obfuscation if it's significant (ignore simple case/space changes)
        normalized_orig = re.sub(r'\s+', '', text.lower())
        normalized_clean = re.sub(r'\s+', '', clean_text.lower())
        
        obfuscation_detected = (normalized_orig != normalized_clean) or (len(decoded_texts) > 0)
        
        if obfuscation_detected:
            keywords = ["ignore", "system", "jailbreak", "override", "instruction"]
            all_decoded = [clean_text.lower()] + [d.lower() for d in decoded_texts]
            for d in all_decoded:
                if any(k in d for k in keywords):
                    max_decoded_rule_score = max(max_decoded_rule_score, 45.0) # At least a WARNING

        if max_decoded_rule_score >= 40:
            # If the decoded text contains a high-risk pattern, force it to 100% (BLOCK)
            max_decoded_rule_score = 100.0

        combined_score = max(final_rule_score, ml_data["score"], max_decoded_rule_score)
        
        # Determine the most relevant threat type
        threat_type = "NLP Pattern"
        if "HARMFUL" in contexts: threat_type = "Harmful Content"
        elif "SYSTEM" in contexts: threat_type = "System Bypass"
        elif "HACKING" in contexts: threat_type = "Cyber Attack"
        elif "ROLEPLAY" in contexts: threat_type = "Jailbreak/Roleplay"
        elif "DATA_EXFIL" in contexts: threat_type = "Data Leak"
        elif obfuscation_detected: threat_type = "Obfuscation"
        elif combined_score < 30: threat_type = "Benign"

        classification = "SAFE"
        if combined_score > 70: classification = "BLOCK"
        elif combined_score > 30: classification = "WARNING"
            
        return {
            "score": combined_score,
            "ml_score": round(ml_data["score"], 4),
            "rule_score": round(max(final_rule_score, max_decoded_rule_score), 4),
            "classification": classification,
            "threat_type": threat_type,
            "detected_contexts": contexts,
            "patterns_matched": list(set(rule_data["patterns_found"] + clean_rule_data["patterns_found"])),
            "obfuscation_detected": obfuscation_detected,
            "base64_detected": any(re.match(r'(?:[A-Za-z0-9+/]{4}){2,}', text) for text in [text] + decoded_texts)
        }
