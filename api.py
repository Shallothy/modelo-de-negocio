from flask import Flask, request, jsonify
from chatbot_grj import responder_mensagem

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def webhook_chat():
    dados = request.get_json() or {}
    remetente = dados.get("remetente")
    mensagem = dados.get("mensagem")
    tipo_agente = dados.get("tipo_agente", "secretaria_grj") # Agente padrão

    try:
        # Passa o tipo de agente desejado para o cérebro
        texto_resposta = responder_mensagem(
            mensagem=mensagem, 
            id_usuario=remetente, 
            agente=tipo_agente
        )
        return jsonify({"resposta": texto_resposta}), 200

    except Exception as e:
        print(f"\n❌ [FALHA NO AGENTE {tipo_agente}]: {e}")
        return jsonify({
            "resposta": "Olá! Nosso assistente virtual está passando por uma breve atualização. Em instantes um atendente falará com você!"
        }), 200

if __name__ == "__main__":
    print("\n✓ Servidor da API GRJ pronto!")
    print("🚀 API do WhatsApp conectada ao Gemini rodando na porta 5000...\n")
    app.run(host="127.0.0.1", port=5000)