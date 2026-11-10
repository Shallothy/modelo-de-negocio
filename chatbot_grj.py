import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database.database import cadastrar_lead_interessado, agendar_demonstracao, verificar_cliente_existente

load_dotenv()

chave_gemini = os.getenv("GEMINI_API_KEY", "").strip()
if not chave_gemini:
    raise ValueError("Chave GEMINI_API_KEY não foi encontrada no arquivo .env!")

client = genai.Client(api_key=chave_gemini)

system_instruction = """
Você é a secretária virtual oficial da GRJ no WhatsApp, uma empresa especializada no desenvolvimento e venda de chatbots inteligentes para microempresas.
O grande diferencial da GRJ: oferecemos chatbots com a mesma qualidade e inteligência de grandes empresas, mas com planos acessíveis para microempreendedores.

Diretrizes:
- Responda sempre em português do Brasil com tom acolhedor, profissional e ágil.
- Mostre como o chatbot ajuda a não perder clientes no WhatsApp, automatiza agendamentos e atende 24/7.
- Quando o cliente demonstrar interesse ou passar seus dados (nome, empresa, nicho), use a ferramenta `cadastrar_lead_interessado`.
- Se ele quiser agendar uma demonstração, use a ferramenta `agendar_demonstracao`.
- Mantenha respostas dinâmicas e sem blocos gigantes de texto.
"""

MODELOS_DISPONIVEIS = [
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash"
]

sessoes_ativas = {}

def obter_chat(id_usuario: str, modelo: str):
    chave_sessao = f"{id_usuario}_{modelo}"
    if chave_sessao not in sessoes_ativas:
        sessoes_ativas[chave_sessao] = client.chats.create(
            model=modelo,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                tools=[cadastrar_lead_interessado, agendar_demonstracao, verificar_cliente_existente]
            )
        )
    return sessoes_ativas[chave_sessao]

def responder_mensagem(mensagem: str, id_usuario: str = "terminal") -> str:
    """
    Tenta responder usando o modelo principal. Se o Google der erro 503 (high demand),
    recorre automaticamente aos modelos reservas.
    """
    ultimo_erro = None

    for modelo in MODELOS_DISPONIVEIS:
        for tentativa in range(2):
            try:
                chat = obter_chat(id_usuario, modelo)
                resposta = chat.send_message(mensagem)
                return resposta.text
            except Exception as e:
                erro_str = str(e)
                ultimo_erro = erro_str
                if "503" in erro_str or "high demand" in erro_str.lower() or "unavailable" in erro_str.lower():
                    print(f"⚠️ Modelo {modelo} em alta demanda. Tentando contingência...")
                    time.sleep(1.2)
                    continue
                else:
                    raise e

    raise RuntimeError(f"Todos os modelos da Google estão temporariamente ocupados: {ultimo_erro}")


# =====================================================================
# 🟢 BLOCO QUE FALTAVA PARA INICIALIZAR O CHATBOT NO TERMINAL:
# =====================================================================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🤖 SECRETÁRIA VIRTUAL DA GRJ INICIALIZADA!")
    print("Digite 'sair' a qualquer momento para finalizar.")
    print("=" * 50 + "\n")

    while True:
        pergunta = input("Você: ")
        
        if pergunta.strip().lower() in ["sair", "exit", "quit"]:
            print("\nSecretária GRJ: Foi um prazer atender você! Até logo.")
            break
            
        if not pergunta.strip():
            continue

        try:
            resposta = responder_mensagem(pergunta, id_usuario="terminal")
            print(f"\nSecretária GRJ:\n{resposta}\n")
        except Exception as e:
            print(f"\nErro ao responder: {e}\n")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🤖 SECRETÁRIA VIRTUAL DA GRJ INICIALIZADA!")
    print("Digite 'sair' a qualquer momento para finalizar.")
    print("=" * 50 + "\n")
    while True:
        pergunta = input("Você: ")
        
        if pergunta.strip().lower() in ["sair", "exit", "quit"]:
            print("\nSecretária GRJ: Foi um prazer atender você! Até logo.")
            break
            
        if not pergunta.strip():
            continue
        try:
            resposta = responder_mensagem(pergunta, id_usuario="terminal")
            print(f"\nSecretária GRJ:\n{resposta}\n")
        except Exception as e:
            print(f"\nErro ao responder: {e}\n")