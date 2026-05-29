import os
import requests
from dotenv import load_dotenv

load_dotenv()
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")

def test_v1():
    # Another common pattern for the API
    url = "https://api-inference.huggingface.co/pipeline/text-generation/gpt2"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": "The internet was created by"}
    res = requests.post(url, headers=headers, json=payload)
    print(f"V1 Test - Status: {res.status_code}, Response: {res.text[:100]}")

test_v1()
