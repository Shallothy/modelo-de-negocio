import json

from chatbot_grj import responder_mensagem
from database.persistencia_sqlite import (
    SessionLocal,
    SessaoUsuario,
    ConversaLog,
    inicializar_banco
)

def executar_simulador():
    inicializar_banco()

    cenarios = [
        {
            "titulo": "CENÁRIO 1: Fluxo Padrão, API REST e Agendamento",
            "usuario_id": "cliente_fluxo_padrao",
            "mensagens": [
                "Olá, quanto custam os planos do chatbot?",
                "Quero agendar uma demonstração. Meu nome é Rodrigo, da empresa TechNiterói, telefone 21999999999, para amanhã às 14h."
            ]
        },
        {
            "titulo": "CENÁRIO 2: Robustez NLU com Gírias e Erros Ortográficos",
            "usuario_id": "cliente_ruido_nlu",
            "mensagens": [
                "oi, queria ta agendando umas demonstracoes pra minha loja",
                "quanto tao custando os planos ai?"
            ]
        },
        {
            "titulo": "CENÁRIO 3: Fallback (2 Falhas Consecutivas) e Transbordo Humano",
            "usuario_id": "cliente_fallback",
            "mensagens": [
                "Hoje está fazendo muito calor aqui.",
                "Qual foi o placar do jogo ontem?",
                "Oi, ainda tem alguém aí?"
            ]
        },
        {
            "titulo": "CENÁRIO 4: Transbordo Imediato por Insatisfação/Urgência",
            "usuario_id": "cliente_urgencia",
            "mensagens": [
                "Estou insatisfeito, quero falar com um atendente humano."
            ]
        }
    ]

    print("\n" + "=" * 60)
    print("🚀 INICIANDO SIMULAÇÃO COMPLETA DOS CENÁRIOS DO MANUAL")
    print("=" * 60)

    for cenario in cenarios:
        print(f"\n>>> {cenario['titulo']} (ID: {cenario['usuario_id']})")
        print("-" * 60)
        for msg in cenario["mensagens"]:
            print(f"👤 Usuário: {msg}")
            resposta = responder_mensagem(msg, id_usuario=cenario["usuario_id"])
            print(f"🤖 Bot: {resposta}\n")

    db = SessionLocal()
    try:
        sessoes = db.query(SessaoUsuario).all()
        logs = db.query(ConversaLog).all()

        print("=" * 60)
        print(f"🗄️ AUDITORIA SQLITE (grj_chatbot.db): {len(sessoes)} sessões | {len(logs)} logs gravados")
        print("=" * 60)

        for s in sessoes:
            print(
                f"• Usuário: {s.usuario_id} | Estado: {s.estado_atual} | "
                f"Falhas: {s.falhas_consecutivas} | Transbordo: {s.transbordo_humano} "
                f"({s.motivo_transbordo or 'N/A'})"
            )
    finally:
        db.close()

if __name__ == "__main__":
    executar_simulador()