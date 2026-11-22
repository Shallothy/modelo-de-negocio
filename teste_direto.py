import os
import requests
from dotenv import load_dotenv

load_dotenv()

chave = os.getenv("GEMINI_API_KEY", "").strip()

print(f"Testando chave no cabeçalho: {chave[:8]}... (Total: {len(chave)} caracteres)")

# 1. URL pura sem ?key= no final
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"

# 2. A chave AQ. DEVE ir no cabeçalho 'x-goog-api-key'
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": chave
}

try:
    resposta = requests.post(
        url,
        headers=headers,
        json={"contents": [{"parts": [{"text": "Diga apenas: 'Funcionou!' "}]}]}
    )
    
    print("\n--- RESULTADO COM CABEÇALHO ---")
    print(f"Status Code: {resposta.status_code}")
    print(f"Resposta: {resposta.text}")
    print("--------------------------------")
except Exception as e:
    print(f"Erro: {e}")