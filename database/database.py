import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Carrega o .env caso precise do caminho das credenciais
load_dotenv()

# Caminho do arquivo json baixado do Firebase Console
caminho_credenciais = os.getenv("FIREBASE_CREDENTIALS", "firebase-credentials.json")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(caminho_credenciais)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✓ Conexão com Firebase Firestore estabelecida com sucesso.")
except Exception as e:
    print(f"⚠️ Aviso ao conectar no Firebase: {e}")
    db = None


def cadastrar_lead_interessado(nome: str, telefone: str, nome_empresa: str, ramo_atuacao: str, interesse: str) -> dict:
    """
    Salva os dados de um microempreendedor interessado nos chatbots da GRJ no Firebase.
    
    Parâmetros:
    - nome: Nome da pessoa de contato
    - telefone: WhatsApp ou telefone
    - nome_empresa: Nome do negócio
    - ramo_atuacao: Área de atuação (ex: pizzaria, salão de beleza, clínica, etc.)
    - interesse: O que o cliente busca (ex: plano básico, dúvidas, automação de agendamentos)
    """
    if db is None:
        return {"status": "erro", "mensagem": "Banco de dados indisponível no momento."}
    
    try:
        doc_ref = db.collection("leads_grj").document()
        doc_ref.set({
            "nome": nome,
            "telefone": telefone,
            "nome_empresa": nome_empresa,
            "ramo_atuacao": ramo_atuacao,
            "interesse": interesse,
            "data_registro": firestore.SERVER_TIMESTAMP,
            "status": "novo_lead"
        })
        return {"status": "sucesso", "mensagem": "Lead cadastrado com sucesso no sistema da GRJ."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}


def agendar_demonstracao(nome: str, telefone: str, data_preferida: str) -> dict:
    """
    Agenda um horário de demonstração prática do chatbot para o cliente.
    
    Parâmetros:
    - nome: Nome do cliente
    - telefone: Telefone ou WhatsApp
    - data_preferida: Data e período desejados (ex: '2026-11-12 pela manhã')
    """
    if db is None:
        return {"status": "erro", "mensagem": "Banco de dados indisponível no momento."}
    
    try:
        doc_ref = db.collection("demonstracoes").document()
        doc_ref.set({
            "nome": nome,
            "telefone": telefone,
            "data_preferida": data_preferida,
            "data_solicitacao": firestore.SERVER_TIMESTAMP,
            "status": "pendente_confirmacao"
        })
        return {"status": "sucesso", "mensagem": "Demonstração solicitada e registrada com sucesso."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}