import re
import unicodedata

PADROES_INTENCOES = {
    "atendimento_humano": [
        "falar com atendente",
        "falar com um atendente",
        "falar com uma pessoa",
        "atendimento humano",
        "quero um humano",
        "falar com alguem",
        "nao quero falar com robo",
        "estou insatisfeito",
        "pessimo atendimento",
        "urgente"
    ],
    "agendar_demonstracao": [
        "agendar demonstracao",
        "marcar demonstracao",
        "quero demonstracao",
        "demonstracao do chatbot",
        "marcar reuniao",
        "agendar reuniao"
    ],
    "consultar_precos": [
        "quanto custa",
        "qual o preco",
        "quais os valores",
        "quanto e",
        "valor do chatbot",
        "preco do chatbot",
        "quais sao os planos"
    ],
    "contratar_servico": [
        "quero contratar",
        "quero adquirir",
        "quero comprar",
        "desejo contratar",
        "fechar negocio",
        "fechar contrato"
    ],
    "consultar_servicos": [
        "quais servicos",
        "conhecer os servicos",
        "como funciona",
        "o que o chatbot faz",
        "quero saber mais",
        "conhecer a empresa"
    ]
}

LEMAS_INTENCOES = {
    "atendimento_humano": [
        {"falar", "atendente"},
        {"falar", "humano"},
        {"falar", "pessoa"},
        {"atendimento", "humano"},
        {"insatisfeito"},
        {"urgente"}
    ],
    "agendar_demonstracao": [
        {"agendar", "demonstracao"},
        {"marcar", "demonstracao"},
        {"querer", "demonstracao"},
        {"agendar", "reuniao"},
        {"marcar", "reuniao"}
    ],
    "consultar_precos": [
        {"quanto", "custar"},
        {"qual", "preco"},
        {"qual", "valor"},
        {"valor", "chatbot"},
        {"preco", "chatbot"},
        {"plano"}
    ],
    "contratar_servico": [
        {"querer", "contratar"},
        {"querer", "adquirir"},
        {"querer", "comprar"},
        {"fechar", "contrato"},
        {"fechar", "negocio"}
    ],
    "consultar_servicos": [
        {"servico", "oferecer"},
        {"conhecer", "servico"},
        {"como", "funcionar"},
        {"conhecer", "empresa"}
    ]
}

def normalizar_texto(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def classificar_intencao(mensagem: str, lemas: list[str] | None = None) -> str:
    if not isinstance(mensagem, str) or not mensagem.strip():
        return "intencao_nao_identificada"

    texto_norm = normalizar_texto(mensagem)

    for intencao, padroes in PADROES_INTENCOES.items():
        for padrao in padroes:
            padrao_norm = normalizar_texto(padrao)
            if re.search(r"(?<!\w)" + re.escape(padrao_norm) + r"(?!\w)", texto_norm):
                return intencao

    if lemas:
        conjunto_lemas = {normalizar_texto(lema) for lema in lemas}
        for intencao, grupos_lemas in LEMAS_INTENCOES.items():
            for grupo in grupos_lemas:
                if grupo.issubset(conjunto_lemas):
                    return intencao

    return "intencao_nao_identificada"