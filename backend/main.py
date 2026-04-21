import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from detection import DetectionEngine
from sanitization import SanitizationEngine

from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

app = FastAPI(title="Prompt Injection Detection System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
detection_engine = DetectionEngine()
sanitization_engine = SanitizationEngine()

# Configure Hugging Face
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
# Using the specific model path for better reliability
client_hf = InferenceClient(model="openai-community/gpt2", token=hf_api_key)

class AnalysisRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_input(request: AnalysisRequest):
    result = detection_engine.get_combined_score(request.text)
    return result

@app.post("/sanitize")
async def sanitize_input(request: AnalysisRequest):
    sanitized_text = sanitization_engine.sanitize(request.text)
    return {"original": request.text, "sanitized": sanitized_text}

@app.post("/chat")
async def chat(request: ChatRequest):
    # 1. Analyze
    analysis = detection_engine.get_combined_score(request.text)
    print(f"DEBUG: Analysis for '{request.text[:20]}...': {analysis['classification']} (Score: {analysis['score']})")
    
    # 2. Decide
    if analysis["classification"] == "BLOCK":
        return {
            "analysis": analysis,
            "response": "BLOCK: Your input was identified as a security risk and has been blocked.",
            "sanitized_text": None
        }
    
    # 3. Sanitize if Warning
    text_to_send = request.text
    sanitized_text = None
    if analysis["classification"] == "WARNING":
        sanitized_text = sanitization_engine.sanitize(request.text)
        text_to_send = sanitized_text
        
    # 4. Generate Response
    if analysis["classification"] == "SAFE":
        # Force the 2-line professional response for SAFE prompts as requested
        bot_response = (
            f"The prompt '{request.text[:30]}' has been scanned and verified as SAFE.\n"
            "AI Security Shield confirmed no malicious injection patterns or adversarial instructions were detected."
        )
    else:
        # For WARNING level, we still try the AI but fallback if it fails
        try:
            bot_response = client_hf.text_generation(
                text_to_send,
                max_new_tokens=80,
                return_full_text=False
            )
            if not bot_response: raise Exception("No response")
        except Exception:
            bot_response = (
                f"Input '{request.text[:30]}' was sanitized due to security warnings.\n"
                "Potentially dangerous keywords were neutralized to ensure a secure processing environment."
            )

    return {
        "analysis": analysis,
        "response": bot_response,
        "sanitized_text": sanitized_text
    }

@app.get("/")
async def root():
    return {"message": "Prompt Injection Detection API is running with GPT-Neo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
