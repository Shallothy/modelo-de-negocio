import time
import requests
from database.database import db

URL_DISPARO_WHATSAPP = "http://127.0.0.1:3001/enviar-ativo"

def chamar_novos_leads_firebase():
    """
    Busca todos os leads com status 'novo_lead' no Firestore
    e envia a primeira mensagem ativa pelo WhatsApp.
    """
    if db is None:
        print("❌ Banco de dados Firebase indisponível.")
        return

    print("\n🔍 Buscando novos leads no Firebase para contato ativo...")
    
    docs = db.collection("leads_grj").where("status", "==", "novo_lead").stream()
    
    leads_encontrados = False

    for doc in docs:
        leads_encontrados = True
        dados = doc.to_dict()
        doc_id = doc.id
        
        nome = dados.get("nome", "Amigo(a)")
        telefone = dados.get("telefone_limpo") or dados.get("telefone")
        empresa = dados.get("nome_empresa", "sua empresa")

        mensagem = (
            f"Olá {nome}, tudo bem? Aqui é a secretária virtual da GRJ! 👋\n\n"
            f"Vi que você demonstrou interesse em automatizar o atendimento da {empresa}. "
            "Gostaria de agendar uma demonstração rápida de 10 minutos para ver como nosso chatbot "
            "funciona na prática e aumenta suas vendas?"
        )

        print(f"📲 Chamando {nome} no número {telefone}...")

        try:
            resposta = requests.post(
                URL_DISPARO_WHATSAPP,
                json={"telefone": telefone, "mensagem": mensagem},
                timeout=10
            )

            if resposta.status_code == 200:
                db.collection("leads_grj").document(doc_id).update({
                    "status": "contatado",
                    "contatado_em": requests.utils.default_user_agent() # ou data atual
                })
                print(f"✅ Mensagem entregue com sucesso para {nome}! Status atualizado no Firebase.")
            else:
                print(f"⚠️ Não foi possível chamar {nome}: {resposta.json().get('erro')}")

        except Exception as e:
            print(f"❌ Erro ao conectar com o WhatsApp: {e}")

        time.sleep(3.5)

    if not leads_encontrados:
        print("ℹ️ Nenhum novo lead pendente encontrado no Firebase.")

if __name__ == "__main__":
    chamar_novos_leads_firebase()