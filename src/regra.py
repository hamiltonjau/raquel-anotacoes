"""Regra das anotações — pura: sem internet, sem Streamlit, sem planilha.

A planilha é só o cofre. Toda a decisão (o que é um item, o que é "feito", qual
o tipo da folha, como somar preço) mora aqui — e é por isso que dá para testar
sem tocar no Google.

Formato de uma linha na planilha (as 8 colunas, sempre nesta ordem):
    A Feito | B Item | C Qtd | D Preco | E Quando | F Prioridade | G Detalhe
    H Foto (links do Drive, separados por espaço — 1 por foto)
"""
import re
import unicodedata

COLUNAS = ["Feito", "Item", "Qtd", "Preco", "Quando", "Prioridade", "Detalhe", "Foto"]
N_COLUNAS = len(COLUNAS)

PRIORIDADES = ["Alta", "Média", "Baixa"]

LIMITE_ITEM = 200
LIMITE_CAMPO = 120
LIMITE_DETALHE = 500
LIMITE_FOTO = 2000          # cabe muita foto: cada link tem ~60 caracteres

# Cada tipo diz quais campos extras a tela mostra e como chamá-los.
TIPOS = {
    "compras": {
        "rotulo": "Compras",
        "emoji": "🛒",
        "campos": ["qtd", "preco", "detalhe"],
        "rotulos": {"qtd": "Qtd", "preco": "Preço", "detalhe": "Onde / obs."},
        "dica": "o que comprar",
        "palavras": ["compra", "mercado", "feira", "supermercado"],
    },
    "tarefas": {
        "rotulo": "Tarefas",
        "emoji": "✅",
        "campos": ["quando", "prioridade", "detalhe"],
        "rotulos": {"quando": "Prazo", "prioridade": "Prioridade", "detalhe": "Comentário"},
        "dica": "o que fazer",
        "palavras": ["tarefa", "fazer", "afazer", "to do", "pendencia"],
    },
    "lembretes": {
        "rotulo": "Lembretes",
        "emoji": "🔔",
        "campos": ["quando", "detalhe"],
        "rotulos": {"quando": "Quando", "detalhe": "Comentário"},
        "dica": "do que lembrar",
        "palavras": ["lembrete", "lembrar", "aviso", "agenda"],
    },
    # "Vendas e Recebimentos" (20/10/2026): mesmo formato de conta das compras
    # (quantidade + valor), mas com o rótulo certo para quem vende.
    "vendas": {
        "rotulo": "Vendas",
        "emoji": "💰",
        "campos": ["qtd", "preco", "detalhe"],
        "rotulos": {"qtd": "Qtd", "preco": "Valor", "detalhe": "Cliente / obs."},
        "dica": "o que foi vendido",
        "palavras": ["venda", "vendas", "recebimento", "recebimentos", "receber"],
    },
    # "Consultas e Exames": data + com quem/onde.
    "consultas": {
        "rotulo": "Consultas",
        "emoji": "🩺",
        "campos": ["quando", "detalhe"],
        "rotulos": {"quando": "Quando", "detalhe": "Médico / local"},
        "dica": "qual consulta ou exame",
        "palavras": ["consulta", "consultas", "exame", "exames", "medico", "medica"],
    },
    "simples": {
        "rotulo": "Lista",
        "emoji": "📋",
        "campos": ["detalhe"],
        "rotulos": {"detalhe": "Detalhe"},
        "dica": "o que anotar",
        "palavras": [],
    },
}

TIPOS_VALIDOS = tuple(TIPOS)


# ---------------------------------------------------------------- texto


def sem_acento(texto: str) -> str:
    """'Média' -> 'media' (para comparar nome de folha sem depender de acento)."""
    decomposto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def limpar(valor, limite: int = LIMITE_CAMPO) -> str:
    """Tira espaços sobrando (inclusive os "invisíveis" do celular) e corta o tamanho."""
    texto = " ".join(str(valor or "").replace("\u00a0", " ").split())
    texto = texto.replace("\n", " ").strip()
    return texto[:limite]


def chave(texto: str) -> str:
    """Chave de comparação: sem acento, minúscula, sem pontuação."""
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento(texto).lower()).strip()


# ---------------------------------------------------------------- tipos


def tipo_por_nome(nome: str, mapa: dict | None = None) -> str:
    """Descobre o tipo de uma folha pelo nome (ou pelo mapa vindo da `_config`)."""
    if mapa:
        achado = mapa.get(nome)
        if achado in TIPOS:
            return achado
    alvo = chave(nome)
    for tipo, dados in TIPOS.items():
        for palavra in dados["palavras"]:
            if palavra in alvo:
                return tipo
    return "simples"


def campos_do_tipo(tipo: str) -> list[str]:
    return list(TIPOS.get(tipo, TIPOS["simples"])["campos"])


def rotulo_do_campo(tipo: str, campo: str) -> str:
    return TIPOS.get(tipo, TIPOS["simples"])["rotulos"].get(campo, campo.capitalize())


def emoji_do_tipo(tipo: str) -> str:
    return TIPOS.get(tipo, TIPOS["simples"])["emoji"]


# ---------------------------------------------------------------- números


def preco_num(valor) -> float | None:
    """Lê preço do jeito que aparece na planilha: 18,9 / 18.90 / R$ 1.234,56."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        numero = float(valor)
        return numero if numero > 0 else None
    texto = str(valor).replace("R$", "").replace("\u00a0", "").strip()
    if not texto:
        return None
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):        # 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        else:                                          # 1,234.56
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    texto = re.sub(r"[^0-9.\-]", "", texto)
    try:
        numero = float(texto)
    except ValueError:
        return None
    return numero if numero > 0 else None


def preco_texto(valor) -> str:
    """18.9 -> '18,90' (é assim que escrevemos na planilha)."""
    numero = preco_num(valor)
    return "" if numero is None else f"{numero:.2f}".replace(".", ",")


def preco_brl(valor) -> str:
    numero = preco_num(valor)
    if numero is None:
        return ""
    inteiro, centavos = f"{numero:.2f}".split(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return "R$ " + ".".join(grupos) + "," + centavos


# ---------------------------------------------------------------- linhas


def _booleano(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return bool(valor)
    texto = str(valor or "").strip().lower()
    if texto in {"✓", "✔", "☑"}:
        return True
    return chave(texto) in {"true", "sim", "x", "1", "verdadeiro", "feito", "ok"}


def _prioridade(valor) -> str:
    alvo = chave(str(valor or ""))
    for p in PRIORIDADES:
        if chave(p) == alvo:
            return p
    return {"a": "Alta", "m": "Média", "b": "Baixa", "1": "Alta", "2": "Média", "3": "Baixa"}.get(alvo, "")


def para_item(linha: int, valores) -> dict:
    """Linha da planilha -> item da tela. `linha` é o número real na planilha."""
    v = list(valores) + [""] * (N_COLUNAS - len(valores))
    return {
        "linha": int(linha),
        "feito": _booleano(v[0]),
        "item": limpar(v[1], LIMITE_ITEM),
        "qtd": limpar(v[2]),
        "preco": preco_num(v[3]),
        "quando": limpar(str(v[4] or "").lstrip("'")),   # apóstrofo = "texto" na planilha
        "prioridade": _prioridade(v[5]),
        "detalhe": limpar(v[6], LIMITE_DETALHE),
        "foto": fotos_de(v[7]),
    }


def para_linha(item: dict) -> list:
    """Item da tela -> linha da planilha (7 colunas, na ordem fixa)."""
    return [
        bool(item.get("feito")),
        limpar(item.get("item"), LIMITE_ITEM),
        limpar(item.get("qtd")),
        preco_num(item.get("preco")) or "",      # número: no Sheets vira valor (dá para somar)
        _texto_forcado(item.get("quando")),      # data como texto: não vira número de série
        item.get("prioridade") if item.get("prioridade") in PRIORIDADES else "",
        limpar(item.get("detalhe"), LIMITE_DETALHE),
        " ".join(fotos_do_item(item))[:LIMITE_FOTO].strip(),
    ]


def _texto_forcado(valor) -> str:
    """Apostrofo na frente = "isto é texto" para o Sheets (não adivinha data)."""
    texto = limpar(valor, LIMITE_CAMPO)
    return ("'" + texto) if texto else ""


def fotos_de(valor) -> str:
    """Célula da coluna Foto -> links (um por foto), separados por espaço."""
    if isinstance(valor, (list, tuple)):
        pedacos = [str(x) for x in valor]
    else:
        pedacos = str(valor or "").split()
    links = [p.strip() for p in pedacos if p.strip().startswith("http")]
    return " ".join(links)[:LIMITE_FOTO]


def fotos_do_item(item: dict) -> list[str]:
    """Links das fotos de um item (lista, já sem lixo)."""
    return fotos_de((item or {}).get("foto")).split()


def linha_vazia(valores) -> bool:
    return not any(str(x).strip() for x in valores)


def ler_itens(valores: list, primeira_linha: int = 2) -> list[dict]:
    """Todas as linhas (menos o cabeçalho) -> itens. Ignora linha totalmente vazia."""
    itens = []
    for deslocamento, valores_linha in enumerate(valores or []):
        if linha_vazia(valores_linha):
            continue
        item = para_item(primeira_linha + deslocamento, valores_linha)
        if item["item"] or item["detalhe"] or item["preco"]:
            itens.append(item)
    return itens


def conferir(itens: list[dict], linha: int, texto: str) -> dict:
    """Acha o item por linha E confere o texto.

    Lição da página de Ideias: antes de mexer, confirmar que a linha ainda é
    aquela. Se não bater (outro aparelho mexeu no meio), recusa em vez de
    escrever na linha errada.
    """
    for item in itens:
        if item["linha"] == int(linha):
            if (item["item"] or item["detalhe"]) != (texto or ""):
                raise ValueError("A linha mudou enquanto você mexia. Atualize a página.")
            return item
    raise ValueError("Não achei essa linha. Atualize a página.")


# ---------------------------------------------------------------- resumo


def separar(itens: list[dict]) -> tuple[list[dict], list[dict]]:
    """(a fazer, feitos) — mantendo a ordem da planilha."""
    return ([i for i in itens if not i["feito"]], [i for i in itens if i["feito"]])


def resumo(itens: list[dict], tipo: str = "simples") -> str:
    """'3 a fazer · R$ 38,20' — só o que faz sentido para o tipo."""
    a_fazer, _ = separar(itens)
    partes = [f"{len(a_fazer)} a fazer" if len(a_fazer) != 1 else "1 a fazer"]
    if "preco" in campos_do_tipo(tipo):
        total = sum(i["preco"] or 0 for i in a_fazer)
        if total:
            partes.append(preco_brl(total))
    return " · ".join(partes)


def etiqueta(item: dict, tipo: str) -> str:
    """A linha de "meta" embaixo do item: 1 pct · R$ 18,90 · mercado."""
    pedacos = []
    if "qtd" in campos_do_tipo(tipo) and item.get("qtd"):
        pedacos.append(item["qtd"])
    if "preco" in campos_do_tipo(tipo) and item.get("preco"):
        pedacos.append(preco_brl(item["preco"]))
    if "quando" in campos_do_tipo(tipo) and item.get("quando"):
        pedacos.append(("prazo " if tipo == "tarefas" else "") + item["quando"])
    if item.get("detalhe"):
        pedacos.append(item["detalhe"])
    if "prioridade" in campos_do_tipo(tipo) and item.get("prioridade"):
        pedacos.append(item["prioridade"])
    return " · ".join(pedacos)


# ---------------------------------------------------------------- nome de folha


def nome_folha_valido(nome: str) -> str:
    """Devolve o nome arrumado ou levanta ValueError com o motivo."""
    nome = limpar(nome, 60)
    if not nome:
        raise ValueError("Dê um nome para a folha.")
    if len(nome) < 2:
        raise ValueError("O nome da folha está curto demais.")
    if re.search(r"[\[\]\*\?/\\:]", nome):
        raise ValueError("O nome da folha não pode ter [ ] * ? / \\ :")
    if chave(nome) in {"config", "como usar"}:
        raise ValueError("Esse nome é reservado — escolha outro.")
    return nome


def nome_de_aba(nome: str) -> str:
    """Nome da folha -> título de aba na planilha (o Sheets limita a 100)."""
    return limpar(nome, 90) or "Folha"
