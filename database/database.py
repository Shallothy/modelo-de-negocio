import os
import re
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

caminho_credenciais = os.getenv("FIREBASE_CREDENTIALS", "./firebase/firebase.json")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(caminho_credenciais)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✓ Conexão com Firebase Firestore estabelecida com sucesso.")
except Exception as e:
    print(f"⚠️ Aviso ao conectar no Firebase: {e}")
    db = None


def validar_formato_telefone(telefone: str) -> bool:
    """Valida se o telefone brasileiro possui DDD + 8 ou 9 dígitos válidos."""
    apenas_numeros = re.sub(r"\D", "", telefone)
    if apenas_numeros.startswith("55") and len(apenas_numeros) in [12, 13]:
        apenas_numeros = apenas_numeros[2:]
    return len(apenas_numeros) in [10, 11]


def verificar_cliente_existente(telefone: str) -> dict:
    """Consulta se o número já tem cadastro no Firebase."""
    if db is None:
        return {"status": "erro", "mensagem": "Banco de dados indisponível."}

    tel_limpo = re.sub(r"\D", "", telefone)
    try:
        docs = db.collection("leads_grj").where("telefone_limpo", "==", tel_limpo).stream()
        leads = [doc.to_dict() for doc in docs]
        
        if leads:
            cliente = leads[0]
            return {
                "encontrado": True,
                "nome": cliente.get("nome"),
                "empresa": cliente.get("nome_empresa"),
                "mensagem": f"Cliente já cadastrado como {cliente.get('nome')} da empresa {cliente.get('nome_empresa')}."
            }
        return {"encontrado": False, "mensagem": "Cliente novo, sem cadastro prévio."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}


def cadastrar_lead_interessado(nome: str, telefone: str, nome_empresa: str, ramo_atuacao: str, interesse: str) -> dict:
    """Valida o telefone e salva o lead no Firebase."""
    if db is None:
        return {"status": "erro", "mensagem": "Banco de dados indisponível."}

    if not validar_formato_telefone(telefone):
        return {
            "status": "invalido",
            "mensagem": "Telefone inválido. Peça gentilmente o número com o DDD para o cliente."
        }

    tel_limpo = re.sub(r"\D", "", telefone)
    try:
        consulta = verificar_cliente_existente(telefone)
        if consulta.get("encontrado"):
            return {
                "status": "ja_existe",
                "mensagem": f"O cliente {nome} já possui cadastro no sistema da GRJ."
            }

        doc_ref = db.collection("leads_grj").document()
        doc_ref.set({
            "nome": nome,
            "telefone": telefone,
            "telefone_limpo": tel_limpo,
            "nome_empresa": nome_empresa,
            "ramo_atuacao": ramo_atuacao,
            "interesse": interesse,
            "data_registro": firestore.SERVER_TIMESTAMP,
            "status": "novo_lead"
        })
        return {"status": "sucesso", "mensagem": "Lead validado e cadastrado com sucesso no Firebase."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

def agendar_demonstracao(nome: str, telefone: str, data_preferida: str) -> dict:
    """Valida o telefone e agenda um horário de demonstração no Firebase."""
    if db is None:
        return {"status": "erro", "mensagem": "Banco de dados indisponível."}

    if not validar_formato_telefone(telefone):
        return {
            "status": "invalido",
            "mensagem": "Telefone inválido. Peça o número completo com DDD para confirmar o agendamento."
        }

    tel_limpo = re.sub(r"\D", "", telefone)
    try:
        doc_ref = db.collection("demonstracoes").document()
        doc_ref.set({
            "nome": nome,
            "telefone": telefone,
            "telefone_limpo": tel_limpo,
            "data_preferida": data_preferida,
            "data_solicitacao": firestore.SERVER_TIMESTAMP,
            "status": "pendente_confirmacao"
        })
        return {"status": "sucesso", "mensagem": f"Demonstração solicitada para {nome} em {data_preferida}."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
