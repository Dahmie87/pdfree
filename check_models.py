from groq import Groq  # type: ignore
import os
from dotenv import load_dotenv  # type: ignore
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
models = client.models.list()
for model in models.data:
    print(model.id)
