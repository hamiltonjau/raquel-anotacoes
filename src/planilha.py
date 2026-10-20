"""A planilha como cofre: ler, escrever, criar folha e arrumar o formato.

Quem decide o que é item, o que é "feito" e o que é preço é `regra.py`.
Aqui só se conversa com o Google — e todo erro vira `ErroAnotacoes` com uma
frase que o Hamilton entende (nada de stack trace na tela).
"""
import time

from . import regra
from .config import ABA_CONFIG, FOLHAS_PADRAO, NOME_PLANILHA


class ErroAnotacoes(Exception):
    """Erro para mostrar na tela, em português."""


# ------------------------------------------------------------------ utilidades


def _aba(titulo: str) -> str:
    """'Minhas coisas' -> 'Minhas coisas' (com aspas simples, do jeito do Sheets)."""
    return "'" + str(titulo).replace("'", "''") + "'"


def _com_retry(funcao, tentativas: int = 3):
    """Uma queda de rede não pode perder a anotação do Hamilton."""
    erro = None
    for tentativa in range(tentativas):
        try:
            return funcao()
        except Exception as falha:               # HttpError, timeout, DNS...
            erro = falha
            texto = str(falha)
            if "403" in texto or "404" in texto:  # permissão: repetir não resolve
                break
            time.sleep(0.6 * (tentativa + 1))
    raise ErroAnotacoes(_traduzir(erro))


def _traduzir(erro) -> str:
    texto = str(erro)
    if "403" in texto or "PERMISSION_DENIED" in texto:
        return ("A planilha não está liberada para o robô. No Drive, clique em "
                "Compartilhar e dê acesso de **Editor** ao e-mail do robô.")
    if "404" in texto or "NOT_FOUND" in texto:
        return ("Não achei a planilha (ou o acesso foi removido). Confira se ela "
                "continua compartilhada com o robô.")
    if "429" in texto or "quota" in texto.lower():
        return "O Google pediu calma (muitas chamadas). Espere alguns segundos e tente de novo."
    if "timed out" in texto.lower() or "TimeoutError" in texto:
        return "A internet demorou demais para responder. Tente de novo."
    return f"Deu erro ao falar com o Google: {texto[:180]}"


# ------------------------------------------------------------------ achar a planilha


def achar_planilha(dr, nome: str = NOME_PLANILHA, email_robo: str = "") -> dict:
    """Procura, entre as planilhas compartilhadas com o robô, a que tem este nome."""
    def listar():
        return dr.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            fields="files(id,name,modifiedTime)", pageSize=200,
            includeItemsFromAllDrives=True, supportsAllDrives=True,
            orderBy="modifiedTime desc",
        ).execute()

    arquivos = _com_retry(listar).get("files", [])
    iguais = [a for a in arquivos if regra.chave(a.get("name", "")) == regra.chave(nome)]
    if not iguais:
        dica = (f"Compartilhe a planilha com **{email_robo}** (Editor)." if email_robo
                else "Compartilhe a planilha com o e-mail do robô (Editor).")
        raise ErroAnotacoes(
            f"Não achei nenhuma planilha chamada **{nome}** compartilhada comigo.\n\n"
            f"1. No Drive, crie a planilha **{nome}** (dentro da pasta *anotações*).\n"
            f"2. Clique em **Compartilhar** → {dica}\n"
            f"3. Volte aqui e toque em 🔄."
        )
    # Se houver mais de uma com o mesmo nome, vale a mexida por último.
    return iguais[0]


# ------------------------------------------------------------------ abas


def folhas(sh, sid: str) -> list[dict]:
    """Todas as abas: [{'titulo','gid','oculta'}, ...] na ordem da planilha."""
    def ler():
        return sh.spreadsheets().get(
            spreadsheetId=sid,
            fields="sheets(properties(sheetId,title,hidden))",
        ).execute()

    meta = _com_retry(ler)
    saida = []
    for aba in meta.get("sheets", []):
        p = aba.get("properties", {})
        saida.append({
            "titulo": p.get("title", ""),
            "gid": p.get("sheetId"),
            "oculta": bool(p.get("hidden")),
        })
    return saida


def folhas_visiveis(sh, sid: str) -> list[dict]:
    return [f for f in folhas(sh, sid) if not f["oculta"] and f["titulo"] != ABA_CONFIG]


# ------------------------------------------------------------------ itens


def _valores(sh, sid: str, intervalo: str) -> list:
    def ler():
        return sh.spreadsheets().values().get(
            spreadsheetId=sid, range=intervalo,
            valueRenderOption="FORMATTED_VALUE",   # o que o olho vê ("18,90", "22/10/2026")
        ).execute()

    return _com_retry(ler).get("values", [])


def ler_itens(sh, sid: str, titulo: str) -> list[dict]:
    valores = _valores(sh, sid, f"{_aba(titulo)}!A2:H")
    return regra.ler_itens(valores, primeira_linha=2)


def adicionar(sh, sid: str, titulo: str, item: dict) -> int:
    """Grava na primeira linha livre (logo abaixo do último item).

    Nada de `append` do Sheets: ele manda a linha para depois da "tabela" que o
    próprio Sheets acha que existe (com o formato até a linha 1000, o item ia
    parar na 1001 — lista longe do cabeçalho). Devolve a linha usada.
    """
    itens = ler_itens(sh, sid, titulo)
    proxima = (max(i["linha"] for i in itens) + 1) if itens else 2
    gravar_item(sh, sid, titulo, proxima, item)
    return proxima


def gravar_item(sh, sid: str, titulo: str, linha: int, item: dict) -> None:
    linha = int(linha)
    alvo = f"{_aba(titulo)}!A{linha}:H{linha}"

    def escrever():
        return sh.spreadsheets().values().update(
            spreadsheetId=sid, range=alvo,
            valueInputOption="USER_ENTERED",
            body={"values": [regra.para_linha(item)]},
        ).execute()

    _com_retry(escrever)


def gravar_foto(sh, sid: str, titulo: str, linha: int, links: list[str]) -> None:
    """Grava os links das fotos na coluna H (só nela — o resto da linha não muda)."""
    alvo = f"{_aba(titulo)}!H{int(linha)}"
    texto = " ".join(str(x) for x in links)

    def escrever():
        return sh.spreadsheets().values().update(
            spreadsheetId=sid, range=alvo, valueInputOption="RAW",
            body={"values": [[texto]]},
        ).execute()

    _com_retry(escrever)


def marcar(sh, sid: str, titulo: str, linha: int, feito: bool) -> None:
    alvo = f"{_aba(titulo)}!A{int(linha)}"

    def escrever():
        return sh.spreadsheets().values().update(
            spreadsheetId=sid, range=alvo, valueInputOption="USER_ENTERED",
            body={"values": [[bool(feito)]]},
        ).execute()

    _com_retry(escrever)


def apagar(sh, sid: str, gid: int, linha: int) -> None:
    """Apaga a linha de verdade (não deixa buraco na planilha)."""
    corpo = {"requests": [{"deleteDimension": {"range": {
        "sheetId": int(gid), "dimension": "ROWS",
        "startIndex": int(linha) - 1, "endIndex": int(linha),
    }}}]}

    def apagar_linha():
        return sh.spreadsheets().batchUpdate(spreadsheetId=sid, body=corpo).execute()

    _com_retry(apagar_linha)


# ------------------------------------------------------------------ config (tipo de cada folha)


def ler_config(sh, sid: str) -> dict:
    try:
        valores = _valores(sh, sid, f"{_aba(ABA_CONFIG)}!A2:B")
    except ErroAnotacoes:
        return {}
    mapa = {}
    for linha in valores:
        if len(linha) >= 2 and linha[0]:
            mapa[str(linha[0])] = str(linha[1])
    return mapa


def gravar_config(sh, sid: str, mapa: dict) -> None:
    corpo = [[nome, tipo] for nome, tipo in mapa.items()]
    valores = [["Folha", "Tipo"]] + corpo

    # Limpa antes de escrever: `update` só cobre as linhas que recebe, então uma
    # folha que saiu do mapa deixaria a linha velha para trás (achado em
    # 19/10/2026, ao apagar uma folha de teste).
    def limpar():
        return sh.spreadsheets().values().clear(
            spreadsheetId=sid, range=f"{_aba(ABA_CONFIG)}!A2:B",
        ).execute()

    def escrever():
        return sh.spreadsheets().values().update(
            spreadsheetId=sid, range=f"{_aba(ABA_CONFIG)}!A1:B",
            valueInputOption="RAW", body={"values": valores},
        ).execute()

    try:
        _com_retry(limpar)
    except ErroAnotacoes:
        pass                                   # aba vazia/recém-criada: nada a limpar
    _com_retry(escrever)


def _garantir_config(sh, sid: str) -> int:
    """Cria a aba escondida `_config` se ela não existir. Devolve o gid."""
    for aba in folhas(sh, sid):
        if aba["titulo"] == ABA_CONFIG:
            return aba["gid"]
    pedido = {"requests": [{"addSheet": {"properties": {
        "title": ABA_CONFIG, "hidden": True,
        "gridProperties": {"rowCount": 200, "columnCount": 2},
    }}}]}

    def criar():
        return sh.spreadsheets().batchUpdate(spreadsheetId=sid, body=pedido).execute()

    resposta = _com_retry(criar)
    gid = resposta["replies"][0]["addSheet"]["properties"]["sheetId"]
    gravar_config(sh, sid, {})
    return gid


# ------------------------------------------------------------------ criar / arrumar folha


def _formato(gid: int, tipo: str) -> list[dict]:
    """Deixa a folha bonita também no Sheets (cabeçalho, caixinha, larguras)."""
    def coluna(inicio: int, fim: int, linhas: tuple[int, int] | None = None):
        faixa = {"sheetId": gid, "startColumnIndex": inicio, "endColumnIndex": fim}
        if linhas:
            faixa["startRowIndex"], faixa["endRowIndex"] = linhas
        return faixa

    larguras = [42, 260, 80, 100, 110, 100, 240, 160]
    pedidos = [
        {"repeatCell": {
            "range": coluna(0, regra.N_COLUNAS, (0, 1)),
            "cell": {"userEnteredFormat": {
                "backgroundColor": {"red": 0.902, "green": 0.957, "blue": 0.918},
                "textFormat": {"bold": True, "foregroundColor": {"red": 0.043, "green": 0.42, "blue": 0.227}},
                "verticalAlignment": "MIDDLE",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
        }},
        {"updateSheetProperties": {
            "properties": {"sheetId": gid, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }},
    ]
    # Nada de "caixinha" (validação BOOLEAN) na coluna inteira: o Sheets
    # preenche FALSE em todas as linhas do intervalo (medido em 19/10 — a lista
    # ia parar na linha 1000). A marcação é feita pelo app, com TRUE/FALSE de
    # verdade, linha por linha.
    for indice, largura in enumerate(larguras):
        pedidos.append({"updateDimensionProperties": {
            "range": {"sheetId": gid, "dimension": "COLUMNS",
                      "startIndex": indice, "endIndex": indice + 1},
            "properties": {"pixelSize": largura}, "fields": "pixelSize",
        }})
    if "preco" in regra.campos_do_tipo(tipo):
        pedidos.append({"repeatCell": {
            "range": coluna(3, 4, (1, 1000)),
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "R$ #,##0.00"}}},
            "fields": "userEnteredFormat.numberFormat",
        }})
    if "prioridade" in regra.campos_do_tipo(tipo):
        pedidos.append({"setDataValidation": {
            "range": coluna(5, 6, (1, 1000)),
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": p} for p in regra.PRIORIDADES]},
                "strict": False, "showCustomUi": True,
            },
        }})
    return pedidos


def formatar(sh, sid: str, gid: int, tipo: str) -> None:
    corpo = {"requests": _formato(int(gid), tipo)}

    def enviar():
        return sh.spreadsheets().batchUpdate(spreadsheetId=sid, body=corpo).execute()

    _com_retry(enviar)


def _escrever_cabecalho(sh, sid: str, titulo: str) -> None:
    def escrever():
        return sh.spreadsheets().values().update(
            spreadsheetId=sid, range=f"{_aba(titulo)}!A1:H1",
            valueInputOption="RAW", body={"values": [regra.COLUNAS]},
        ).execute()

    _com_retry(escrever)


def criar_folha(sh, sid: str, nome: str, tipo: str = "simples") -> int:
    """Cria uma aba nova com cabeçalho e formato. Devolve o gid."""
    nome = regra.nome_de_aba(regra.nome_folha_valido(nome))
    pedido = {"requests": [{"addSheet": {"properties": {
        "title": nome, "gridProperties": {"frozenRowCount": 1},
    }}}]}

    def criar():
        return sh.spreadsheets().batchUpdate(spreadsheetId=sid, body=pedido).execute()

    try:
        resposta = _com_retry(criar)
    except ErroAnotacoes:
        raise ErroAnotacoes(f"Já existe uma folha chamada **{nome}** (ou o nome não foi aceito).")
    gid = resposta["replies"][0]["addSheet"]["properties"]["sheetId"]
    _escrever_cabecalho(sh, sid, nome)
    formatar(sh, sid, gid, tipo)
    return gid


def _marcar_tipo(sh, sid: str, nome: str, tipo: str) -> None:
    mapa = ler_config(sh, sid)
    mapa[nome] = tipo
    gravar_config(sh, sid, mapa)


def criar_folha_e_anotar(sh, sid: str, nome: str, tipo: str = "simples") -> str:
    """Cria a folha e guarda o tipo dela. Devolve o nome final da aba."""
    gid = criar_folha(sh, sid, nome, tipo)
    final = regra.nome_de_aba(regra.nome_folha_valido(nome))
    _marcar_tipo(sh, sid, final, tipo)
    return final


def _renomear(sh, sid: str, gid: int, nome: str) -> None:
    corpo = {"requests": [{"updateSheetProperties": {
        "properties": {"sheetId": int(gid), "title": nome},
        "fields": "title",
    }}]}

    def renomear():
        return sh.spreadsheets().batchUpdate(spreadsheetId=sid, body=corpo).execute()

    _com_retry(renomear)


_EH_PADRAO = {"sheet1", "pagina1", "planilha1", "ignorar", "folha1", "sheet"}


def _aba_em_branco(sh, sid: str, titulo: str) -> bool:
    if regra.chave(titulo) not in _EH_PADRAO:
        return False
    valores = _valores(sh, sid, f"{_aba(titulo)}!A1:G5")
    return all(regra.linha_vazia(v) for v in valores)


def garantir_estrutura(sh, sid: str) -> str:
    """Primeira vez numa planilha: cria as folhas padrão (ou adota as que existem).

    Devolve um aviso curto para a tela (ou "").
    """
    abas = folhas(sh, sid)
    visiveis = [a for a in abas if not a["oculta"] and a["titulo"] != ABA_CONFIG]
    tem_config = any(a["titulo"] == ABA_CONFIG for a in abas)
    config = ler_config(sh, sid) if tem_config else {}

    # 1) Planilha em branco (uma aba "Sheet1"/"Página1" vazia) -> vira o padrão.
    if len(visiveis) == 1 and _aba_em_branco(sh, sid, visiveis[0]["titulo"]):
        primeira = visiveis[0]
        nome, tipo = FOLHAS_PADRAO[0]
        _renomear(sh, sid, primeira["gid"], nome)
        formatar(sh, sid, primeira["gid"], tipo)
        _escrever_cabecalho(sh, sid, nome)
        config[nome] = tipo
        for outro_nome, outro_tipo in FOLHAS_PADRAO[1:]:
            criar_folha(sh, sid, outro_nome, outro_tipo)
            config[outro_nome] = outro_tipo
        _garantir_config(sh, sid)
        gravar_config(sh, sid, config)
        return f"Preparei as {len(FOLHAS_PADRAO)} folhas na sua planilha."

    # 2) Planilha sem nenhuma aba visível -> cria todas as padrão.
    if not visiveis:
        for nome, tipo in FOLHAS_PADRAO:
            criar_folha(sh, sid, nome, tipo)
            config[nome] = tipo
        _garantir_config(sh, sid)
        gravar_config(sh, sid, config)
        return f"Preparei as {len(FOLHAS_PADRAO)} folhas na sua planilha."

    # 3) Já tem folhas: só anota o tipo de cada uma (sem mexer no visual dele).
    mudou = False
    for aba in visiveis:
        if aba["titulo"] not in config:
            config[aba["titulo"]] = regra.tipo_por_nome(aba["titulo"], config)
            mudou = True
    if not tem_config:
        _garantir_config(sh, sid)
        mudou = True
    if mudou:
        gravar_config(sh, sid, config)
    return ""


def tipo_da_folha(sh, sid: str, titulo: str, config: dict | None = None) -> str:
    mapa = config if config is not None else ler_config(sh, sid)
    return regra.tipo_por_nome(titulo, mapa)
