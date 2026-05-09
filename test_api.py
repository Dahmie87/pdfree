import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")

# Test multiple models to find one that works
test_models = [
    "mistralai/Mistral-7B-Instruct-v0.2",  # Newer Mistral
    "meta-llama/Llama-2-7b-chat-hf",       # Meta Llama
    "mistral-community/Mistral-7B-Instruct-v0.2",  # Community version
    "gpt2",                                 # Smallest, most available
]

url = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print(f"Testing HuggingFace Inference Providers API with multiple models...")
print()

for model_id in test_models:
    print(f"{'='*60}")
    print(f"Testing: {model_id}")

    payload = {
        "model": f"{model_id}:fastest",
        "messages": [
            {
                "role": "user",
                "content": "Hello, say hi back"
            }
        ],
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers,
                                 json=payload, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Response: {data['choices'][0]['message']['content']}")
            break
        else:
            data = response.json()
            print(
                f"❌ Error: {data.get('error', {}).get('message', response.text)[:100]}")
    except Exception as e:
        print(f"Exception: {str(e)[:100]}")

    print()
