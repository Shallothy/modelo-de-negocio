import spacy

from nlp.classificador_intencoes import classificar_intencao

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    raise RuntimeError(
        "Modelo de português não encontrado. "
        "Execute: python -m spacy download pt_core_news_sm"
    )

def analisar_mensagem(texto: str) -> dict:
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("A mensagem não pode estar vazia.")

    doc = nlp(texto)

    tokens = [token.text for token in doc if not token.is_space]

    tokens_filtrados = [
        token.text
        for token in doc
        if not token.is_space and not token.is_punct and not token.is_stop
    ]

    lemas = [
        token.lemma_.lower()
        for token in doc
        if not token.is_space
        and not token.is_punct
        and not token.is_stop
        and token.lemma_
    ]

    entidades = [
        {"texto": entidade.text, "tipo": entidade.label_}
        for entidade in doc.ents
    ]

    intencao = classificar_intencao(texto, lemas=lemas)

    return {
        "mensagem_original": texto,
        "tokens": tokens,
        "tokens_filtrados": tokens_filtrados,
        "lemas": lemas,
        "entidades": entidades,
        "intencao": intencao
    }