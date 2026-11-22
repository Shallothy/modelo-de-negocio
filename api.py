from flask import Flask, request, jsonify
from chatbot_grj import responder_mensagem
from database.persistencia_sqlite import inicializar_banco

app = Flask(__name__)
inicializar_banco()

@app.route("/", methods=["GET"])
def home():
    return "<h1>🟢 API da Secretária Virtual GRJ está ONLINE e pronta no WhatsApp!</h1>", 200

@app.route("/api/planos", methods=["GET"])
def obter_planos():
    """Endpoint REST dinâmico consumido via requests pelo chatbot (Eixo 2)."""
    return jsonify({
        "empresa": "GRJ Chatbots Inteligentes",
        "moeda": "BRL",
        "planos": [
            {
                "nome": "Plano Start",
                "preco_mensal": 149.90,
                "recursos": ["Atendimento 24/7 no WhatsApp", "Agendamento automático", "Suporte comercial"]
            },
            {
                "nome": "Plano Pro",
                "preco_mensal": 249.90,
                "recursos": ["Tudo do Start", "Integração CRM/Firebase", "Relatórios e transbordo humano"]
            }
        ]
    }), 200

@app.route("/chat", methods=["POST"])
def webhook_chat():
    dados = request.get_json() or {}
    remetente = dados.get("remetente")
    mensagem = dados.get("mensagem")
    tipo_agente = dados.get("tipo_agente", "secretaria_grj")

    if not remetente or not mensagem:
        return jsonify({"erro": "Campos 'remetente' e 'mensagem' são obrigatórios."}), 400

    try:
        texto_resposta = responder_mensagem(
            mensagem=mensagem,
            id_usuario=remetente,
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