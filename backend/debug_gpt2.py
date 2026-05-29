import os
import requests
from dotenv import load_dotenv

load_dotenv()
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")

def query_hf(prompt, model_id="openai-community/gpt2"):
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    response = requests.post(api_url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        return response.text

test_prompts = [
    "Explain the history of the Internet."
]

for p in test_prompts:
    print(f"\n--- Testing with openai-community/gpt2: ---\n{p}")
    result = query_hf(p)
    print(f"Result: {result}")
