import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"Token: {api_key[:20] if api_key else 'NOT SET'}...")

# Use official HF library
client = InferenceClient(api_key=api_key)

# Start with the simplest model
model_id = "gpt2"

print(f"\nTesting: {model_id}")

try:
    response = client.text_generation(
        "Hello",
        model=model_id,
        max_new_tokens=50
    )
    print(f"✅ SUCCESS!")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Error type: {type(e).__name__}")
    print(f"❌ Full error:\n{e}")
    import traceback
    traceback.print_exc()

