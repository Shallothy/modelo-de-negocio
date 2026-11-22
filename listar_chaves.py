import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

chave = os.getenv("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=chave)

print("\n--- MODELOS DISPONÍVEIS NA SUA CONTA ---")
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(f"👉 {model.name}")
print("----------------------------------------\n")