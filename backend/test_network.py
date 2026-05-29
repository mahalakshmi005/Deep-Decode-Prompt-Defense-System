import requests
response = requests.get("https://huggingface.co/api/models/gpt2")
print(f"Status: {response.status_code}")
print(f"Content: {response.text[:200]}")
