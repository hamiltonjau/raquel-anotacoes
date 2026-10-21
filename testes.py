"""Testes do Anotações.

    ./.venv/bin/python testes.py            # regra (offline, rápido)
    ./.venv/bin/python testes.py --real     # + uma planilha de teste de verdade
                                            #   (cria, usa e APAGA no Drive do robô)

O teste "real" é o que pega o que só aparece falando com o Google: formato de
preço/data, cabeçalho, permissão, apagar linha.
"""
import sys
import time

from src import regra
from src import planilha as pl

FALHAS: list[str] = []
PASSOS = 0


def ok(nome: str, condicao, detalhe: str = "") -> None:
    global PASSOS
    PASSOS += 1
    if condicao:
        print(f"  ✓ {nome}")
    else:
        print(f"  ✗ {nome}  {detalhe}")
        FALHAS.append(nome)


def igual(nome: str, visto, esperado) -> None:
    ok(nome, visto == esperado, f"(veio {visto!r}, esperava {esperado!r})")


# ---------------------------------------------------------------- 1. linhas


def teste_linhas() -> None:
    print("\n1. Linha da planilha <-> item da tela")
    linha = [True, "Café", "1 pct", "18,90", "22/10", "Alta", "mercado"]
    item = regra.para_item(2, linha)
    igual("feito", item["feito"], True)
    igual("item", item["item"], "Café")
    igual("preço lido", item["preco"], 18.9)
    igual("quando", item["quando"], "22/10")
    igual("prioridade", item["prioridade"], "Alta")
    igual("detalhe", item["detalhe"], "mercado")

    volta = regra.para_linha(item)
    igual("volta tem 8 colunas", len(volta), regra.N_COLUNAS)
    igual("volta item", volta[1], "Café")
    igual("volta preço é número", volta[3], 18.9)
    igual("volta data vira texto (apóstrofo)", volta[4], "'22/10")
    re_lido = regra.para_item(2, volta)
    igual("data volta igual (apóstrofo não aparece)", re_lido["quando"], "22/10")


def teste_fotos() -> None:
    print("\n1b. Fotos (coluna H) — links do Drive")
    item = regra.para_item(2, [False, "Dentista", "", "", "25/10/2026", "", "", 
                               "https://drive.google.com/file/d/AAA/view https://drive.google.com/file/d/BBB/view"])
    igual("2 fotos lidas", len(regra.fotos_do_item(item)), 2)
    ok("primeira foto certa",
       regra.fotos_do_item(item)[0].endswith("AAA/view"))
    igual("lixo é descartado", regra.fotos_de("  oi  https://x/y  lixo"), "https://x/y")
    igual("célula vazia", regra.fotos_do_item({"foto": ""}), [])
    linha = regra.para_linha(item)
    igual("foto vai para a coluna H", linha[7],
          "https://drive.google.com/file/d/AAA/view https://drive.google.com/file/d/BBB/view")
    igual("item sem foto continua funcionando", len(regra.para_linha({"item": "x"})), 8)
    igual("para_item com linha curta não quebra", regra.para_item(2, [False, "x"])["foto"], "")


def teste_preparo() -> None:
    print("\n1c. Foto do celular: reduzir e virar PDF")
    import io

    from PIL import Image

    from src import fotos

    # Uma "foto grande" de celular: 3000x2000 com ruído (não comprime de graça).
    grande = Image.effect_noise((3000, 2000), 90).convert("RGB")
    cru = io.BytesIO()
    grande.save(cru, "JPEG", quality=95)
    cru = cru.getvalue()
    entrada = [{"nome": "IMG_1234.jpg", "dados": cru, "tipo": "image/jpeg"}]

    pdf = fotos.preparar(entrada, como_pdf=True)
    igual("1 foto -> 1 arquivo", len(pdf), 1)
    igual("virou PDF", pdf[0]["tipo"], "application/pdf")
    igual("sufixo .pdf", pdf[0]["sufixo"], ".pdf")
    ok("é PDF de verdade", pdf[0]["dados"][:5] == b"%PDF-")
    ok("ficou bem menor", len(pdf[0]["dados"]) < len(cru) * 0.5,
       f"({len(cru) // 1024} KB -> {len(pdf[0]['dados']) // 1024} KB)")

    jpg = fotos.preparar(entrada, como_pdf=False)
    igual("JPG: 1 arquivo", len(jpg), 1)
    igual("JPG: tipo", jpg[0]["tipo"], "image/jpeg")
    ok("JPG é JPEG de verdade", jpg[0]["dados"][:2] == b"\xff\xd8")
    aberta = Image.open(io.BytesIO(jpg[0]["dados"]))
    ok("JPG reduzido a 1800 px no lado maior",
       max(aberta.size) <= fotos.LADO_MAX, f"({aberta.size})")
    ok("JPG também ficou menor", len(jpg[0]["dados"]) < len(cru) * 0.5)

    duas = fotos.preparar(entrada * 2, como_pdf=True)
    igual("2 fotos -> 1 PDF só", len(duas), 1)
    igual("PDF com 2 páginas", duas[0]["paginas"], 2)

    from src import fotos as f2
    falso_pdf = [{"nome": "exame.pdf", "dados": b"%PDF-1.4 conteudo",
                  "tipo": "application/pdf"}]
    igual("PDF que já veio passa reto", f2.preparar(falso_pdf, como_pdf=True)[0]["dados"],
          b"%PDF-1.4 conteudo")
    ok("HEIC fora da lista (iPhone manda JPEG)", "heic" not in fotos.TIPOS_ACEITOS)
    igual("nome do arquivo com sufixo escolhido",
          fotos.nome_do_arquivo("Consultas", "Dentista", "25/10/2026", sufixo=".pdf"),
          "25-10-2026 - Dentista.pdf")


def teste_booleanos() -> None:
    print("\n2. 'Feito' do jeito que o Sheets devolve")
    for valor in (True, 1, "TRUE", "true", "Sim", "x", "✓", "VERDADEIRO"):
        ok(f"{valor!r} é feito", regra.para_item(2, [valor])["feito"] is True)
    for valor in (False, 0, "", "FALSE", "não", "nao"):
        ok(f"{valor!r} não é feito", regra.para_item(2, [valor])["feito"] is False)


def teste_precos() -> None:
    print("\n3. Preço (o ponto que mais erra)")
    igual("18,90", regra.preco_num("18,90"), 18.9)
    igual("18.90", regra.preco_num("18.90"), 18.9)
    igual("R$ 18,90", regra.preco_num("R$ 18,90"), 18.9)
    igual("R$ 1.234,56", regra.preco_num("R$ 1.234,56"), 1234.56)
    igual("1,234.56", regra.preco_num("1,234.56"), 1234.56)
    igual("número puro", regra.preco_num(7.5), 7.5)
    igual("vazio", regra.preco_num(""), None)
    igual("texto", regra.preco_num("caro"), None)
    igual("zero", regra.preco_num(0), None)
    igual("mostrar", regra.preco_brl(1234.56), "R$ 1.234,56")
    igual("mostrar simples", regra.preco_brl(7.5), "R$ 7,50")
    igual("campo de edição", regra.preco_texto(18.9), "18,90")


def teste_prioridade() -> None:
    print("\n4. Prioridade")
    igual("alta", regra.para_item(2, ["", "", "", "", "", "alta"])["prioridade"], "Alta")
    igual("MÉDIA", regra.para_item(2, ["", "", "", "", "", "MÉDIA"])["prioridade"], "Média")
    igual("m", regra.para_item(2, ["", "", "", "", "", "m"])["prioridade"], "Média")
    igual("vazio", regra.para_item(2, ["", "", "", "", "", ""])["prioridade"], "")
    igual("outro vira vazio", regra.para_item(2, ["", "", "", "", "", "urgente!"])["prioridade"], "")


def teste_tipos() -> None:
    print("\n5. Tipo da folha (pelo nome, ou pelo mapa da _config)")
    igual("Compras do mercado", regra.tipo_por_nome("Compras do mercado"), "compras")
    igual("Mercado", regra.tipo_por_nome("Mercado"), "compras")
    igual("Tarefas a fazer", regra.tipo_por_nome("Tarefas a fazer"), "tarefas")
    igual("A fazer", regra.tipo_por_nome("A fazer"), "tarefas")
    igual("Lembretes", regra.tipo_por_nome("Lembretes"), "lembretes")
    igual("Filmes", regra.tipo_por_nome("Filmes"), "simples")
    igual("acento não importa", regra.tipo_por_nome("LEMBRETES"), "lembretes")
    igual("mapa manda", regra.tipo_por_nome("Filmes", {"Filmes": "compras"}), "compras")
    igual("mapa inválido é ignorado", regra.tipo_por_nome("Filmes", {"Filmes": "xyz"}), "simples")
    igual("campos de compras", regra.campos_do_tipo("compras"), ["qtd", "preco", "detalhe"])
    igual("campos de lembretes", regra.campos_do_tipo("lembretes"), ["quando", "detalhe"])


def teste_lista() -> None:
    print("\n6. Ler a lista e achar a linha certa")
    valores = [
        ["FALSE", "Café", "1 pct", "18,90", "", "", "mercado"],
        ["", "", "", "", "", "", ""],                       # linha vazia: ignora
        ["TRUE", "Arroz", "1 kg", "7,50", "", "", ""],
    ]
    itens = regra.ler_itens(valores)
    igual("2 itens (pulou a vazia)", len(itens), 2)
    igual("primeira linha é 2", itens[0]["linha"], 2)
    igual("segunda linha é 4", itens[1]["linha"], 4)
    a_fazer, feitos = regra.separar(itens)
    igual("1 a fazer", len(a_fazer), 1)
    igual("1 feito", len(feitos), 1)

    igual("conferir bate", regra.conferir(itens, 2, "Café")["item"], "Café")
    for caso, texto in ((2, "Leite"), (99, "Café"), (2, "")):
        try:
            regra.conferir(itens, caso, texto)
            ok(f"conferir recusa linha {caso} com {texto!r}", False, "(não recusou!)")
        except ValueError:
            ok(f"conferir recusa linha {caso} com {texto!r}", True)


def teste_resumo() -> None:
    print("\n7. Resumo e etiqueta")
    valores = [
        ["FALSE", "Café", "1 pct", "18,90", "", "", "mercado"],
        ["FALSE", "Leite", "2 L", "11,80", "", "", ""],
        ["TRUE", "Arroz", "1 kg", "7,50", "", "", ""],
    ]
    itens = regra.ler_itens(valores)
    igual("resumo de compras", regra.resumo(itens, "compras"), "2 a fazer · R$ 30,70")
    igual("resumo de tarefas (sem preço)", regra.resumo(itens, "tarefas"), "2 a fazer")
    igual("etiqueta", regra.etiqueta(itens[0], "compras"), "1 pct · R$ 18,90 · mercado")


def teste_nomes() -> None:
    print("\n8. Nome de folha (o Sheets é chato)")
    for ruim, motivo in (("", "vazio"), ("a", "curto"), ("A/B", "barra"),
                         ("Teste[1]", "colchete"), ("config", "reservado"),
                         ("Como usar", "reservado")):
        try:
            regra.nome_folha_valido(ruim)
            ok(f"recusa {motivo}", False, "(aceitou!)")
        except ValueError:
            ok(f"recusa {motivo}", True)
    igual("arruma espaços", regra.nome_folha_valido("  Filmes  "), "Filmes")
    igual("nome de aba longo", len(regra.nome_de_aba("x" * 200)), 90)


def teste_limites() -> None:
    print("\n9. Limites (celular manda coisa estranha)")
    item = regra.para_item(2, ["", "  Café\u00a0  com   leite  "])
    igual("espaços invisíveis", item["item"], "Café com leite")
    igual("item corta em 200", len(regra.limpar("x" * 500, regra.LIMITE_ITEM)), 200)
    igual("detalhe corta em 500", len(regra.limpar("x" * 900, regra.LIMITE_DETALHE)), 500)
    igual("linha vazia", regra.linha_vazia(["", "  ", ""]), True)
    igual("linha com algo", regra.linha_vazia(["", "x"]), False)


# ---------------------------------------------------------------- real


def teste_real(sid_existente: str | None = None) -> None:
    print("\n10. De verdade: usa a planilha de teste (e apaga, se foi criada aqui)")
    from src.acesso import servicos

    sheets, drive = servicos(arquivo="credentials/service-account.json")
    sid = sid_existente
    criada = False
    if sid:
        print(f"  · usando a planilha de teste: {sid}")
    else:
        nome = f"Teste Anotações (descartável) {int(time.time())}"
        try:
            criada = sheets.spreadsheets().create(
                body={"properties": {"title": nome}},
                fields="spreadsheetId",
            ).execute()["spreadsheetId"]
            sid = criada
            print(f"  · planilha de teste: {sid}")
        except Exception as erro:
            ok("criar planilha (o robô não tem Drive!)", False,
               f"({type(erro).__name__}: {str(erro)[:120]}...)\n"
               "     -> passe o id de uma planilha já compartilhada: "
               "testes.py --real <id>")
            return

    try:
        aviso = pl.garantir_estrutura(sheets, sid)
        ok("preparou a planilha", bool(aviso), f"(aviso: {aviso!r})")

        abas = pl.folhas_visiveis(sheets, sid)
        titulos = [a["titulo"] for a in abas]
        igual("5 folhas padrão", titulos,
              ["Vendas e Recebimentos", "Consultas e Exames", "Lembretes",
               "Compras do mercado", "Tarefas a fazer"])
        igual("config criada", sorted(pl.ler_config(sheets, sid)),
              sorted(titulos))

        # nada de item fantasma
        igual("começa vazia", pl.ler_itens(sheets, sid, "Compras do mercado"), [])

        # adicionar (com preço e data) e ler de volta
        pl.adicionar(sheets, sid, "Compras do mercado",
                     {"item": "Café", "qtd": "1 pct", "preco": "18,90",
                      "detalhe": "mercado do bairro"})
        pl.adicionar(sheets, sid, "Compras do mercado",
                     {"item": "Leite", "qtd": "2 L", "preco": 11.8})
        itens = pl.ler_itens(sheets, sid, "Compras do mercado")
        igual("2 itens", len(itens), 2)
        igual("primeiro item na linha 2 (colado no cabeçalho)", itens[0]["linha"], 2)
        igual("segundo item na linha 3", itens[1]["linha"], 3)
        igual("preço voltou do Sheets", itens[0]["preco"], 18.9)
        igual("qtd voltou", itens[0]["qtd"], "1 pct")
        igual("etiqueta pronta", regra.etiqueta(itens[0], "compras"),
              "1 pct · R$ 18,90 · mercado do bairro")

        # marcar
        pl.marcar(sheets, sid, "Compras do mercado", itens[0]["linha"], True)
        itens = pl.ler_itens(sheets, sid, "Compras do mercado")
        igual("marcou o café", itens[0]["feito"], True)
        igual("o leite continua pendente", itens[1]["feito"], False)

        # editar (linha + texto conferido)
        café = regra.conferir(itens, itens[0]["linha"], "Café")
        café["item"] = "Café em pó"
        café["preco"] = 21.5
        pl.gravar_item(sheets, sid, "Compras do mercado", café["linha"], café)
        itens = pl.ler_itens(sheets, sid, "Compras do mercado")
        igual("editou o texto", itens[0]["item"], "Café em pó")
        igual("editou o preço", itens[0]["preco"], 21.5)
        igual("não perdeu o 'feito'", itens[0]["feito"], True)

        # data como texto (não pode virar número de série)
        pl.adicionar(sheets, sid, "Lembretes",
                     {"item": "Pagar a luz", "quando": "05/11/2026"})
        lembretes = pl.ler_itens(sheets, sid, "Lembretes")
        igual("data voltou igual", lembretes[0]["quando"], "05/11/2026")

        # a lista tem de ficar colada no cabeçalho (sem "FALSE" sobrando por aí)
        bruto = pl._valores(sheets, sid, "'Lembretes'!A1:G6")
        iguais = [l for l in bruto if len(l) == 1 and l[0] == "FALSE"]
        igual("sem lixo de caixinha (FALSE) na planilha", iguais, [])
        igual("cabeçalho na linha 1", bruto[0][:3], ["Feito", "Item", "Qtd"])

        # apagar
        gid_compras = next(a["gid"] for a in pl.folhas_visiveis(sheets, sid)
                           if a["titulo"] == "Compras do mercado")
        pl.apagar(sheets, sid, gid_compras, itens[1]["linha"])
        itens = pl.ler_itens(sheets, sid, "Compras do mercado")
        igual("sobrou 1 item", len(itens), 1)
        igual("sobrou o certo", itens[0]["item"], "Café em pó")

        # folha nova, criada pelo app
        final = pl.criar_folha_e_anotar(sheets, sid, "Filmes", "simples")
        igual("criou a folha", final, "Filmes")
        pl.adicionar(sheets, sid, "Filmes", {"item": "Duna 2"})
        igual("anotou na folha nova",
              pl.ler_itens(sheets, sid, "Filmes")[0]["item"], "Duna 2")
        igual("tipo guardado", pl.ler_config(sheets, sid).get("Filmes"), "simples")
        ok("filmes aparece na lista de folhas",
           "Filmes" in [a["titulo"] for a in pl.folhas_visiveis(sheets, sid)])

        # nome repetido é recusado com frase clara
        try:
            pl.criar_folha(sheets, sid, "Filmes", "simples")
            ok("recusa folha repetida", False, "(criou duplicada!)")
        except pl.ErroAnotacoes:
            ok("recusa folha repetida", True)

    finally:
        if criada:
            try:
                drive.files().delete(fileId=sid).execute()
                print("  · planilha de teste apagada")
            except Exception as erro:
                print(f"  ! não consegui apagar a planilha de teste {sid}: {erro}")


# ---------------------------------------------------------------- principal


def principal() -> int:
    print("=" * 62)
    print("  TESTES — Anotações")
    print("=" * 62)
    teste_linhas()
    teste_fotos()
    teste_preparo()
    teste_booleanos()
    teste_precos()
    teste_prioridade()
    teste_tipos()
    teste_lista()
    teste_resumo()
    teste_nomes()
    teste_limites()

    if "--real" in sys.argv:
        resto = [a for a in sys.argv[1:] if not a.startswith("--")]
        try:
            teste_real(resto[0] if resto else None)
        except Exception as erro:
            ok("teste de verdade rodou", False, f"({type(erro).__name__}: {erro})")
    else:
        print("\n10. De verdade: PULADO (rode com --real)")

    print("\n" + "=" * 62)
    if FALHAS:
        print(f"  {len(FALHAS)} FALHA(S) em {PASSOS} verificações:")
        for nome in FALHAS:
            print(f"   - {nome}")
        print("=" * 62)
        return 1
    print(f"  TUDO PASSOU — {PASSOS} verificações")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
