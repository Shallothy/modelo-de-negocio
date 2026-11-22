import os
import json
import time
import requests

from dotenv import load_dotenv
from google import genai
from google.genai import types

from database.database import (
    cadastrar_lead_interessado,
    agendar_demonstracao,
    verificar_cliente_existente
)
from database.persistencia_sqlite import (
    SessionLocal,
    inicializar_banco,
    obter_ou_criar_sessao,
    registrar_log
)
from nlp.processador_nlp import analisar_mensagem

load_dotenv()

chave_gemini = os.getenv("GEMINI_API_KEY", "").strip()
if not chave_gemini:
    raise ValueError("Chave GEMINI_API_KEY não foi encontrada no arquivo .env!")

client = genai.Client(api_key=chave_gemini)

URL_API_PLANOS = os.getenv("URL_API_PLANOS", "http://127.0.0.1:5000/api/planos")

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
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

sessoes_ativas = {}


def consultar_api_planos_externa() -> str:
    """
    Eixo 2 - Integração Sistêmica via API REST (requests):
    Busca tabela de preços e disponibilidade em tempo real tratando falhas de rede.
    """
    try:
        resposta = requests.get(URL_API_PLANOS, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        return f"[Dados atualizados da API GRJ: {json.dumps(dados, ensure_ascii=False)}]"
    except requests.exceptions.RequestException as erro:
        return (
            f"[Aviso técnico: API externa indisponível ({type(erro).__name__}). "
            "Informe os planos padrão: Plano Start R$ 149/mês e Plano Pro R$ 249/mês.]"
        )


def obter_chat(id_usuario: str, modelo: str):
    chave_sessao = f"{id_usuario}_{modelo}"
    if chave_sessao not in sessoes_ativas:
        sessoes_ativas[chave_sessao] = client.chats.create(
            model=modelo,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                tools=[
                    cadastrar_lead_interessado,
                    agendar_demonstracao,
                    verificar_cliente_existente
                ]
            )
        )
    return sessoes_ativas[chave_sessao]

def consultar_llm(prompt_contextualizado: str, id_usuario: str) -> str:
    ultimo_erro = None
    for modelo in MODELOS_DISPONIVEIS:
        for _ in range(2):
            try:
                chat = obter_chat(id_usuario, modelo)
                resposta = chat.send_message(prompt_contextualizado)
                return resposta.text
            except Exception as e:
                erro_str = str(e)
                ultimo_erro = erro_str
                if "503" in erro_str or "high demand" in erro_str.lower() or "unavailable" in erro_str.lower():
                    print(f"⚠️ Modelo {modelo} em alta demanda. Tentando contingência...")
                    time.sleep(0.5)
                    continue
                raise e
    raise RuntimeError(f"Todos os modelos da Google estão temporariamente ocupados: {ultimo_erro}")


def responder_mensagem(mensagem: str, id_usuario: str = "terminal") -> str:
    """
    Orquestra os 4 eixos: NLU -> Persistência/Estado -> Regras/Fallback -> API REST / LLM.
    """
    db_sql = SessionLocal()
    try:
        sessao = obter_ou_criar_sessao(db_sql, id_usuario)

        if sessao.transbordo_humano:
            msg_aguardo = (
                "Seu atendimento já foi transferido para um de nossos especialistas humanos. "
                "Em instantes alguém da equipe GRJ continuará por aqui!"
            )
            registrar_log(db_sql, id_usuario, "usuario", mensagem, sessao.estado_atual)
            registrar_log(db_sql, id_usuario, "bot", msg_aguardo, sessao.estado_atual)
            return msg_aguardo
        
        analise = analisar_mensagem(mensagem)
        intencao = analise["intencao"]
        entidades_json = json.dumps(analise["entidades"], ensure_ascii=False)

        if analise["entidades"]:
            sessao.contexto_entidades = entidades_json

        registrar_log(
            db_sql,
            usuario_id=id_usuario,
            remetente="usuario",
            mensagem=mensagem,
            estado_sessao=sessao.estado_atual,
            intencao=intencao,
            entidades=entidades_json
        )

        if intencao == "atendimento_humano":
            sessao.estado_atual = "TRANSBORDO_HUMANO"
            sessao.transbordo_humano = True
            sessao.motivo_transbordo = "Solicitação direta ou insatisfação detectada pelo NLU"
            db_sql.commit()

            resposta_transbordo = (
                "Entendi perfeitamente! Estou transferindo seu atendimento agora mesmo "
                "para um especialista humano da GRJ. Protocolo registrado!"
            )
            registrar_log(
                db_sql,
                usuario_id=id_usuario,
                remetente="sistema",
                mensagem=resposta_transbordo,
                estado_sessao=sessao.estado_atual,
                intencao=intencao,
                evento_transbordo=True
            )
            return resposta_transbordo

        if intencao == "intencao_nao_identificada":
            sessao.falhas_consecutivas += 1

            if sessao.falhas_consecutivas >= 2:
                sessao.estado_atual = "TRANSBORDO_FALLBACK"
                sessao.transbordo_humano = True
                sessao.motivo_transbordo = "2 falhas consecutivas na identificação de intenção"
                db_sql.commit()

                resposta_fallback = (
                    "Desculpe, ainda não consegui compreender sua solicitação com precisão. "
                    "Para não te fazer perder tempo, acabei de transferir sua conversa para "
                    "um atendente humano da GRJ que vai te ajudar agora mesmo!"
                )
                registrar_log(
                    db_sql,
                    usuario_id=id_usuario,
                    remetente="sistema",
                    mensagem=resposta_fallback,
                    estado_sessao=sessao.estado_atual,
                    intencao=intencao,
                    evento_transbordo=True
                )
                return resposta_fallback

            sessao.estado_atual = "AGUARDANDO_ESCLARECIMENTO"
            db_sql.commit()
            resposta_duvida = (
                "Não consegui entender muito bem o que você precisa. "
                "Você gostaria de conhecer nossos planos, ver como funciona o chatbot ou agendar uma demonstração?"
            )
            registrar_log(
                db_sql,
                usuario_id=id_usuario,
                remetente="bot",
                mensagem=resposta_duvida,
                estado_sessao=sessao.estado_atual,
                intencao=intencao
            )
            return resposta_duvida

        sessao.falhas_consecutivas = 0
        sessao.estado_atual = f"FLUXO_{intencao.upper()}"
        db_sql.commit()

        contexto_api = ""
        if intencao in ["consultar_precos", "consultar_servicos"]:
            contexto_api = consultar_api_planos_externa()

        prompt_enriquecido = (
            f"Mensagem do cliente: {mensagem}\n"
            f"[Metadados NLU -> Intenção: {intencao} | Entidades NER: {entidades_json}]\n"
            f"{contexto_api}"
        ).strip()

        resposta_bot = consultar_llm(prompt_enriquecido, id_usuario)

        registrar_log(
            db_sql,
            usuario_id=id_usuario,
            remetente="bot",
            mensagem=resposta_bot,
            estado_sessao=sessao.estado_atual,
            intencao=intencao
        )
        return resposta_bot

    finally:
        db_sql.close()

if __name__ == "__main__":
    inicializar_banco()
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
            resposta = responder_mensagem(pergunta, id_usuario="terminal_demo")
            print(f"\nSecretária GRJ:\n{resposta}\n")
        except Exception as e:
            print(f"\nErro ao responder: {e}\n")
