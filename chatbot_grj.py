import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import database

load_dotenv()

client = genai.Client()

system_instruction = """
Você é a secretária virtual oficial da GRJ, uma empresa especializada no desenvolvimento e venda de chatbots inteligentes para microempresas.
O grande diferencial da GRJ: oferecemos chatbots com a mesma qualidade, inteligência e robustez das grandes empresas de tecnologia, mas com planos e preços altamente acessíveis, pensados na realidade do microempreendedor.

Seu objetivo:
1. Atender com tom comercial, acolhedor, profissional e focado em negócios.
2. Mostrar as vantagens práticas para o cliente: atendimento 24/7, economia de tempo, não perder vendas no WhatsApp/Instagram e triagem automática.
3. Incentivar o cliente a agendar uma demonstração prática ou deixar o contato.
4. Quando o cliente demonstrar interesse ou informar seus dados (nome, WhatsApp, nicho ou empresa), utilize a ferramenta `cadastrar_lead_interessado` para salvar o lead.
5. Se ele quiser agendar uma demonstração, use a ferramenta `agendar_demonstracao`.
6. Nunca responda assuntos irrelevantes ou fora do escopo da empresa; informe educadamente que mantém foco exclusivo nos serviços de atendimento digital da GRJ.
7. Não divulgue dados confidenciais de outros clientes nem códigos internos da empresa.
"""

try:
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            tools=[database.cadastrar_lead_interessado, database.agendar_demonstracao]
        )
    )

    print("\n--- Secretária Virtual da GRJ (digite 'sair' para finalizar) ---")
    
    while True:
        pergunta_usuario = input("\nVocê: ")
        
        if pergunta_usuario.strip().lower() in ["sair", "exit", "quit"]:
            print("\nEncerrando atendimento... Até logo!")
            break

        if not pergunta_usuario.strip():
            continue

        response = chat.send_message(pergunta_usuario)
        
        print("\nSecretária GRJ:")
        print(response.text)

except Exception as e:
    print(f"\nOcorreu um erro: {e}")
