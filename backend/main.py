import os
import requests
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from detection import DetectionEngine
from sanitization import SanitizationEngine
from transformers import pipeline
from session_logger import log_session_event, get_session_logs

# Load environment variables
load_dotenv()

app = FastAPI(title="Prompt Injection Detection System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
print("Initializing Security Engines...")
detection_engine = DetectionEngine()
sanitization_engine = SanitizationEngine()

# Initialize Local LLM (GPT-2)
print("Loading Local AI Model (GPT-2)... This may take a minute on first run.")
try:
    ai_model = pipeline("text-generation", model="gpt2", device=-1)
    print("AI Model loaded successfully.")
except Exception as e:
    print(f"Error loading local model: {e}")
    ai_model = None

class AnalysisRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    text: str

def filter_output(text: str) -> str:
    """Filters AI output for harmful patterns (OWASP LLM02)."""
    if any(tag in text.lower() for tag in ["<script>", "javascript:", "onload=", "onerror="]):
        return "[SECURITY_NOTICE: Potential malicious script detected in AI output and blocked.]"
    return text

@app.get("/logs")
async def get_logs():
    return get_session_logs()

@app.post("/chat")
async def chat(request: ChatRequest):
    # 1. PII Detection & Redaction Layer (Regex/NER)
    redacted_input, pii_types = sanitization_engine.detect_and_redact_pii(request.text)
    
    # 2. Attack Detection Layer (ML + Rules)
    # Analyze the REDACTED text to avoid false positives on raw PII
    lines = redacted_input.split('\n')
    safe_lines = []
    malicious_segments_removed = False
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
            
        line_analysis = detection_engine.get_combined_score(clean_line)
        if line_analysis["classification"] == "SAFE":
            safe_lines.append(clean_line)
        else:
            malicious_segments_removed = True
    
    # 3. Reconstruct safe prompt
    text_to_send = "\n".join(safe_lines)
    
    if not safe_lines:
        analysis = detection_engine.get_combined_score(redacted_input)
        bot_response = "🚨 CRITICAL BLOCK: Your entire request was identified as malicious."
        log_session_event(request.text, bot_response, analysis, "")
        return {
            "analysis": analysis,
            "response": bot_response,
            "sanitized_text": ""
        }
    
    # 4. Final Analysis & Decision Engine
    if malicious_segments_removed:
        display_analysis = {
            "score": 45.0,
            "ml_score": 0.0,
            "rule_score": 45.0,
            "classification": "WARNING",
            "threat_type": "Injection Sanitized",
            "patterns_matched": ["Multi-part Injection Neutralized"],
            "detected_contexts": ["SECURED"]
        }
    else:
        # Check if we have PII but it's otherwise SAFE
        raw_analysis = detection_engine.get_combined_score(text_to_send)
        if pii_types and raw_analysis["classification"] == "SAFE":
            display_analysis = raw_analysis.copy()
            display_analysis["threat_type"] = f"PII Detected ({', '.join(pii_types)})"
            # Keep score low as it's not an attack
            display_analysis["score"] = min(display_analysis["score"], 20.0) 
        else:
            display_analysis = raw_analysis

    # 5. Generate Response locally
    if ai_model:
        try:
            formatted_prompt = f"Question: {text_to_send}\nAnswer:"
            output = ai_model(formatted_prompt, max_new_tokens=40, num_return_sequences=1, truncation=True)
            
            full_text = output[0]['generated_text']
            if "Answer:" in full_text:
                response_body = full_text.split("Answer:")[1].strip()
            else:
                response_body = full_text.replace(formatted_prompt, "").strip()
            
            bot_response_text = response_body.split('\n')[0]
            
            # Filter Output (OWASP LLM02)
            bot_response_text = filter_output(bot_response_text)
            
            if malicious_segments_removed:
                bot_response = f"[SECURE SCAN: INJECTION BLOCKED] AI: {bot_response_text}"
            else:
                bot_response = f"[SECURE SCAN: CLEAN] AI: {bot_response_text}"
        except Exception as e:
            bot_response = f"Sanitized, but local AI error: {str(e)[:50]}"
    else:
        bot_response = "Security check passed, but AI model failed to load locally."

    log_session_event(request.text, bot_response, display_analysis, text_to_send)

    return {
        "analysis": display_analysis,
        "response": bot_response,
        "sanitized_text": text_to_send
    }

@app.get("/")
async def root():
    return {"message": "Detection API (Local Mode) is online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
