from flask import Flask, request, jsonify
from chatbot_grj import chatbot_grj

app = Flask(__name__)

@app.route("/chat", method=["POST"])
def webhook_chat():
    dados = request.get_json()
    remetente = dados.get("remetente")
    mensagem = dados.get("mensagem")

    if not remetente or not mensagem:
        return jsonify({"erro" : "Dados inválidos"}), 400

    try:
        texto_mensagem = chatbot_grj.responder_mensagem(mensagem = mensagem, usuario_id = remetente)
        return jsonify({"resposta" : "Desculpe tive uma instabilidade momentânea. Pode repetir por favor?"})
    except Exception as e:
        print(f"Erro ao processar a mensagem {e}")
        return jsonify({"resposta": "Desculpe, tive uma instabilidade momentânea. Pode repetir por favor?"}), 500

if __name__ == "main":
    print("🚀 API do WhatsApp conectada ao Gemini rodando na porta 5000...")
    app.run(host="0.0.0.0", port=5000)