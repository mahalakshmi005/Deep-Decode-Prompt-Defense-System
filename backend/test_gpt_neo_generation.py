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

models_to_try = [
    "EleutherAI/gpt-neo-2.7B",
    "EleutherAI/gpt-neo-1.3B",
    "gpt2",
]

for model_name in models_to_try:
    print(f"Trying model: {model_name}...")
    url = f"https://api-inference.huggingface.co/models/{model_name}"
    try:
        response = requests.post(url, headers=headers, json={"inputs": "Say hello"})
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            print(f"Success with {model_name}: {result[0].get('generated_text')}")
            break
        else:
            print(f"Failed with {model_name}: {result}")
    except Exception as e:
        print(f"Error with {model_name}: {e}")
