import os
import requests
from dotenv import load_dotenv

load_dotenv()
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-2.7B"
headers = {"Authorization": f"Bearer {hf_api_key}"}

def query_gpt_neo(payload):
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

print(f"Testing GPT-Neo API connection...")
try:
    response = query_gpt_neo({"inputs": "Hello, how are you?"})
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
