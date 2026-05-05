import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
model_id = os.getenv("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.1")

# NEW Endpoint: OpenAI-compatible format
url = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# OpenAI-compatible payload
payload = {
    "model": f"{model_id}:fastest",
    "messages": [
        {
            "role": "user",
            "content": "Hello, write a short greeting in one sentence."
        }
    ],
    "max_tokens": 100,
    "temperature": 0.7
}

print(f"Testing HuggingFace Inference Providers API...")
print(f"URL: {url}")
print(f"Model: {model_id}:fastest")
print(f"Token: {api_key[:20]}...")
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS!")
        data = response.json()
        print(f"Response: {data['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error:\n{response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
