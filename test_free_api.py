import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")

# Use the FREE old endpoint (not the paid router)
url_base = "https://api-inference.huggingface.co/models"

# Simple models that work on free tier
test_models = [
    "gpt2",
    "distilgpt2", 
    "google/flan-t5-base",
    "facebook/opt-125m",
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print(f"Testing HuggingFace FREE Inference API...")
print()

for model_id in test_models:
    print(f"{'='*60}")
    print(f"Testing: {model_id}")
    
    url = f"{url_base}/{model_id}"
    
    # Correct payload for text-generation task
    payload = {
        "inputs": "Hello world",
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Response: {data}")
            print(f"\n⭐ Working model: {model_id}")
            break
        else:
            print(f"❌ Error: {response.text[:150]}")
    except Exception as e:
        print(f"Exception: {str(e)[:100]}")
    
    print()
