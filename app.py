"""Anotações da Raquel — app pessoal, com senha, guardado numa planilha do Drive.

Cópia do app "Anotações" do Hamilton, com planilha própria (pasta "Raquel
Anotações" no Drive), senha própria e porta própria (8641).

Rode:  ./.venv/bin/python -m streamlit run app.py --server.port 8641
"""
import hmac
import json
import os
import time
import traceback

import streamlit as st

# Se a subida falhar (ex.: dependência que não instalou), mostra o motivo na
# tela em vez do "Oh no" mudo do Streamlit Cloud.
try:
    from src import fotos
    from src import planilha as pl
    from src import regra
    from src.acesso import servicos
    from src.config import NOME_PLANILHA, SERVICE_ACCOUNT_FILE
except Exception:
    st.set_page_config(page_title="Anotações da Raquel (erro)", page_icon="📝")
    st.error("**Não consegui carregar o app.** Se você é o Hamilton, me mande este texto:")
    st.code(traceback.format_exc())
    st.stop()

st.set_page_config(page_title="Anotações da Raquel", page_icon="📝", layout="centered")

CSS = """
<style>
  .block-container { max-width: 680px; padding-top: 1.2rem; padding-bottom: 3rem; }
  h1, h2, h3 { letter-spacing: -.2px; }
  div[data-testid="stCheckbox"] label p { font-size: 1rem; }
  div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; }
  .stButton button, .stFormSubmitButton button { border-radius: 10px; }
  /* <span> e não <div>: div dentro de st.container(border=True) colapsa a altura
     (bug do Streamlit 1.66 visto em 20/10/2026 — as linhas de detalhe se
     sobrepunham). Testado: span = 26px, div = 10px. */
  .meta { color: #6b7280; font-size: .82rem; }
  .meta b { color: #b45309; font-weight: 600; }
  .titulo-folha { display: flex; align-items: baseline; gap: 8px; }
  .titulo-folha .qtd { color: #6b7280; font-size: .85rem; font-weight: 400; }
  /* Item: botõezinhos compactos (✏️ 🗑️), que não roubam o espaço do texto */
  [class*="st-key-linha"] button {
    padding: .1rem .45rem !important;
    min-height: 2.1rem !important;
    line-height: 1.1 !important;
  }
  [class*="st-key-linha"] div[data-testid="stCheckbox"] label p {
    font-size: .98rem; line-height: 1.25;
  }
  .fotos a { color: #1d4ed8; text-decoration: none; }
  .fotos a:hover { text-decoration: underline; }

  /* ---------------- celular ---------------- */
  /* O Streamlit escreve os títulos com seletor mais forte que `h2 {}`; por isso
     o `!important` — sem ele o "## 📝 Anotações da Raquel" ficava em 2,25rem e
     quebrava em duas linhas num celular de 390px (visto na foto de 20/10). */
  @media (max-width: 640px) {
    /* 3.4rem em cima: a barra do Streamlit (⋮⋮ + menu) é fixa e cobria o título */
    .block-container { padding: 3.4rem .7rem 3rem; }
    [data-testid="stMarkdownContainer"] h2 { font-size: 1.32rem !important; margin: .1rem 0; }
    [data-testid="stMarkdownContainer"] h3 { font-size: 1.12rem !important; margin: .35rem 0 .1rem; }
    /* o título da folha + "0 a fazer" precisam caber numa linha só */
    .titulo-folha h3 { font-size: 1.05rem !important; margin: .35rem 0 .1rem; line-height: 1.25; }
    .titulo-folha { flex-wrap: nowrap; gap: 0 6px; }
    .titulo-folha .qtd { white-space: nowrap; font-size: .78rem; flex: 0 0 auto; }
    /* o "Deploy" é botão de quem programa — a Raquel não precisa dele */
    [data-testid="stAppDeployButton"] { display: none !important; }
    /* alvo de toque: nada menor que ~44px de altura */
    .stButton button, .stFormSubmitButton button { min-height: 2.6rem; font-size: 1rem; }
    [class*="st-key-linha"] button { min-height: 2.5rem !important; padding: .2rem .3rem !important; }
    [class*="st-key-linha"] div[data-testid="stCheckbox"] label p { font-size: 1rem; }
    /* o nome do item pode quebrar em 2 linhas; "Hemograma compl…" não ajuda ninguém */
    [class*="st-key-linha"] div[data-testid="stWidgetLabel"] p {
      white-space: normal !important; overflow: visible !important;
      text-overflow: clip !important; line-height: 1.25;
    }
    /* pílulas das folhas: uma linha que rola para o lado (sem barra visível).
       O nome do componente no Streamlit 1.66 é `stButtonGroup` (não "stPills",
       que foi o que tentei primeiro e não pegou). */
    [data-testid="stButtonGroup"] div[role="radiogroup"] {
      flex-wrap: nowrap !important; overflow-x: auto; scrollbar-width: none;
      padding-bottom: 2px;
    }
    [data-testid="stButtonGroup"] div[role="radiogroup"]::-webkit-scrollbar { display: none; }
    [data-testid="stButtonGroup"] button { white-space: nowrap; flex: 0 0 auto; font-size: .86rem; }
    /* formulário: campos altos e sem zoom involuntário do iPhone (16px) */
    input, textarea, select { font-size: 16px !important; }
    div[data-testid="stFileUploaderDropzone"] { padding: .8rem .5rem; }
    /* espaçamento vertical mais curto: mais coisa na tela */
    [data-testid="stVerticalBlock"] { gap: .55rem; }
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------- 🔐 senha

def exigir_senha() -> None:
    """Porta de entrada. A senha vive em st.secrets — nunca no código.

    Este app é publicado na internet: sem esta trava, qualquer um com o link
    leria as anotações pessoais. Não remova.
    """
    try:
        senha_certa = str(st.secrets.get("senha", "") or "")
    except Exception:
        senha_certa = ""

    if not senha_certa:
        st.error(
            "🔐 **App bloqueado — a senha ainda não foi configurada.**\n\n"
            "Defina `senha` em `st.secrets`:\n\n"
            "```toml\nsenha = \"sua_senha_aqui\"\n```\n\n"
            "- **No PC:** arquivo `.streamlit/secrets.toml`\n"
            "- **No Streamlit Cloud:** painel do app → *Settings* → *Secrets*"
        )
        st.stop()

    if st.session_state.get("autorizado"):
        return

    st.markdown("## 📝 Anotações da Raquel")
    st.caption("Área pessoal — informe a senha para entrar.")
    with st.form("login"):
        tentativa = st.text_input("Senha", type="password")
        entrou = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if entrou:
        if hmac.compare_digest(str(tentativa), senha_certa):
            st.session_state["senha_erros"] = 0
            st.session_state["autorizado"] = True
            st.rerun()
        # Senha curta (6 dígitos) + app na internet = precisa de freio. A espera
        # cresce a cada erro (2, 4, 8... até 60 s) — some sozinha se acertar.
        erros = int(st.session_state.get("senha_erros", 0)) + 1
        st.session_state["senha_erros"] = erros
        if erros >= 3:
            espera = min(60, 2 ** (erros - 2))
            st.error(f"Senha incorreta. Espere {espera} s para tentar de novo.")
            time.sleep(espera)
        else:
            st.error("Senha incorreta.")
    st.stop()


# --------------------------------------------------------------- credenciais

def _info_robo() -> dict | None:
    try:
        if "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass
    caminho = SERVICE_ACCOUNT_FILE
    if os.path.exists(caminho):
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except Exception:
            return None
    return None


def _info_oauth() -> dict | None:
    """Token OAuth do dono (fotos). Na nuvem vem dos Secrets, chave `google_oauth`."""
    try:
        if "google_oauth" in st.secrets:
            return dict(st.secrets["google_oauth"])
    except Exception:
        pass
    return None


def _email_robo() -> str:
    info = _info_robo() or {}
    return str(info.get("client_email", ""))


def _conectar():
    """Clientes novos a cada rodada — de propósito.

    ⚠️ **NÃO ponha `@st.cache_resource` aqui.** O `httplib2.Http` que vem dentro
    dos clientes **não é thread-safe** (a própria httplib2 avisa). Com o cache, o
    mesmo cliente era usado por duas rodadas ao mesmo tempo (dois cliques rápidos
    ou duas abas) e o processo abortava com `free(): corrupted unsorted chunks`
    (core dump, 20/10/2026). As **credenciais** seguem em cache dentro de
    `src/acesso.credenciais()` — só os clientes são novos.
    """
    info = _info_robo()
    if not info:
        raise pl.ErroAnotacoes(
            "Não achei a credencial do robô.\n\n"
            "No PC: coloque o JSON em `credentials/service-account.json` "
            "(ou defina `SERVICE_ACCOUNT_FILE` no `.env`).\n\n"
            "Na internet: cole o bloco `[gcp_service_account]` nos *Secrets*."
        )
    return servicos(info=info)


@st.cache_data(ttl=600, show_spinner=False)
def _achar_planilha(_drive, nome: str, email: str) -> dict:
    return pl.achar_planilha(_drive, nome, email)


# --------------------------------------------------------------- tela


def principal() -> None:
    exigir_senha()

    try:
        sheets, drive = _conectar()
    except pl.ErroAnotacoes as erro:
        st.error(str(erro))
        st.stop()

    try:
        planilha = _achar_planilha(drive, NOME_PLANILHA, _email_robo())
    except pl.ErroAnotacoes as erro:
        st.markdown("## 📝 Anotações da Raquel")
        st.error(str(erro))
        if st.button("🔄 Já compartilhei — tentar de novo"):
            st.cache_data.clear()
            st.rerun()
        st.stop()

    sid = planilha["id"]

    try:
        aviso = pl.garantir_estrutura(sheets, sid)
        abas = pl.folhas_visiveis(sheets, sid)
        if not abas:
            # Leitura vazia pode ser soluço da API (aconteceu em 19/10/2026, logo
            # depois de criar uma folha). Tenta mais uma vez antes de assustar.
            time.sleep(1)
            abas = pl.folhas_visiveis(sheets, sid)
        if not abas:
            st.warning("A planilha está sem folhas. Crie uma em *＋ nova folha*.")
            st.stop()
        config = pl.ler_config(sheets, sid)

        # ---- cabeçalho
        st.markdown("## 📝 Anotações da Raquel")
        st.caption(f"Guardado em **{planilha['name']}**, no seu Drive.")
        if aviso and not st.session_state.get("ja_avisei"):
            st.session_state["ja_avisei"] = True
            st.success(aviso)

        nomes = [aba["titulo"] for aba in abas]
        # Folha recém-criada na barra lateral: o pedido é aplicado AQUI, antes de
        # o widget das folhas existir. Escrever em `folha_atual` depois do widget
        # dá StreamlitWidgetAlreadyInstantiatedError (bug achado pelo Hamilton
        # em 19/10/2026: "criar folha" nunca tinha funcionado).
        pedida = st.session_state.pop("folha_pedida", None)
        if pedida and pedida in nomes:
            st.session_state["folha_atual"] = pedida
            aviso_folha = f"Criada a folha **{pedida}**."
        else:
            aviso_folha = None
        atual = _seletor(nomes)
        if aviso_folha:
            st.success(aviso_folha)
        gid = next(a["gid"] for a in abas if a["titulo"] == atual)
        tipo = pl.tipo_da_folha(sheets, sid, atual, config)

        itens = pl.ler_itens(sheets, sid, atual)
        a_fazer, feitos = regra.separar(itens)

        st.markdown(
            f"<div class='titulo-folha'><h3>{regra.emoji_do_tipo(tipo)} {atual}</h3>"
            f"<span class='qtd'>{regra.resumo(itens, tipo)}</span></div>",
            unsafe_allow_html=True,
        )

        # ---- formulário de edição (quando escolheu ✏️)
        if st.session_state.get("editando"):
            _form_edicao(sheets, sid, atual, tipo, gid)
        else:
            _form_novo(sheets, sid, atual, tipo)

        # ---- a lista
        if not a_fazer and not feitos:
            st.info("Nada aqui ainda. Escreva no campo acima e toque em **＋ Adicionar**.")
        for item in a_fazer:
            _desenhar_item(sheets, sid, atual, tipo, item, gid)
        if feitos:
            with st.expander(f"✅ Feitos ({len(feitos)})", expanded=False):
                for item in feitos:
                    _desenhar_item(sheets, sid, atual, tipo, item, gid)
                _limpar_feitos(sheets, sid, atual, gid, feitos)

        _barra_lateral(sheets, sid, atual, planilha)

    except pl.ErroAnotacoes as erro:
        st.error(str(erro))
        if st.button("🔄 Tentar de novo"):
            st.cache_data.clear()
            st.rerun()


def _seletor(nomes: list[str]) -> str:
    chave = "folha_atual"
    lembrada = st.session_state.get("folha_lembrada")
    if st.session_state.get(chave) not in nomes:
        # se a lembrada ainda existe, é nela que a pessoa estava
        st.session_state[chave] = lembrada if lembrada in nomes else nomes[0]
    if hasattr(st, "pills"):
        escolhida = st.pills("Folha", nomes, key=chave, label_visibility="collapsed")
    else:                                       # Streamlit antigo
        indice = nomes.index(st.session_state[chave])
        escolhida = st.radio("Folha", nomes, index=indice, horizontal=True,
                             label_visibility="collapsed")
    if escolhida in nomes:
        st.session_state["folha_lembrada"] = escolhida
        return escolhida
    # Pílula é TOGGLE: um segundo toque na folha atual DESMARCA (volta None).
    # Antes ela caía calada na primeira folha e o item ia para a folha errada
    # (medido em 20/10/2026). Agora volta para a última folha de verdade.
    destino = lembrada if lembrada in nomes else nomes[0]
    st.session_state[chave] = destino
    st.rerun()
    return destino                               # (não chega aqui)


# --------------------------------------------------------------- campos


def _campos(tipo: str, prefixo: str, valores: dict) -> dict:
    """Desenha os campos extras do tipo e devolve o que foi preenchido."""
    saida = {}
    campos = regra.campos_do_tipo(tipo)
    if "qtd" in campos:
        saida["qtd"] = st.text_input(
            regra.rotulo_do_campo(tipo, "qtd"), value=valores.get("qtd", ""),
            placeholder="1 kg, 2 L…", key=f"{prefixo}_qtd")
    if "preco" in campos:
        saida["preco"] = st.text_input(
            regra.rotulo_do_campo(tipo, "preco"), value=regra.preco_texto(valores.get("preco")),
            placeholder="18,90", key=f"{prefixo}_preco")
    if "quando" in campos:
        saida["quando"] = st.text_input(
            regra.rotulo_do_campo(tipo, "quando"), value=valores.get("quando", ""),
            placeholder="dd/mm/aaaa — ou 'quando chegar'", key=f"{prefixo}_quando")
    if "prioridade" in campos:
        opcoes = ["—"] + regra.PRIORIDADES
        atual = valores.get("prioridade") or "—"
        escolha = st.selectbox(
            regra.rotulo_do_campo(tipo, "prioridade"), opcoes,
            index=opcoes.index(atual) if atual in opcoes else 0, key=f"{prefixo}_pri")
        saida["prioridade"] = "" if escolha == "—" else escolha
    if "detalhe" in campos:
        saida["detalhe"] = st.text_input(
            regra.rotulo_do_campo(tipo, "detalhe"), value=valores.get("detalhe", ""),
            placeholder="opcional", key=f"{prefixo}_det")
    return saida


def _montar(texto: str, extras: dict, feito: bool = False) -> dict:
    item = regra.limpar(texto, regra.LIMITE_ITEM)
    if not item:
        raise ValueError("Escreva alguma coisa antes de adicionar.")
    return {
        "feito": feito,
        "item": item,
        "qtd": regra.limpar(extras.get("qtd", "")),
        "preco": regra.preco_num(extras.get("preco", "")),
        "quando": regra.limpar(extras.get("quando", "")),
        "prioridade": extras.get("prioridade", "") or "",
        "detalhe": regra.limpar(extras.get("detalhe", ""), regra.LIMITE_DETALHE),
    }


def _form_novo(sheets, sid: str, folha: str, tipo: str) -> None:
    dica = regra.TIPOS.get(tipo, regra.TIPOS["simples"])["dica"]
    with st.form("novo_item", clear_on_submit=True):
        texto = st.text_input("O que anotar", placeholder=dica, label_visibility="visible")
        extras = _campos(tipo, "novo", {})
        enviar = st.form_submit_button("＋ Adicionar", type="primary", use_container_width=True)
    if enviar:
        try:
            item = _montar(texto, extras)
            pl.adicionar(sheets, sid, folha, item)
            st.rerun()
        except ValueError as erro:
            st.warning(str(erro))


def _form_edicao(sheets, sid: str, folha: str, tipo: str, gid: int) -> None:
    item = st.session_state["editando"]
    with st.container(border=True):
        st.markdown("**✏️ Editando**")
        with st.form("editar_item"):
            texto = st.text_input("O que anotar", value=item.get("item", ""))
            extras = _campos(tipo, f"ed{item['linha']}", item)
            b1, b2 = st.columns(2)
            salvar = b1.form_submit_button("Salvar", type="primary", use_container_width=True)
            apagar = b2.form_submit_button("Apagar", use_container_width=True)

        if salvar or apagar:
            try:
                atuais = pl.ler_itens(sheets, sid, folha)
                regra.conferir(atuais, item["linha"], item.get("item") or item.get("detalhe"))
                if apagar:
                    pl.apagar(sheets, sid, gid, item["linha"])
                else:
                    novo = _montar(texto, extras, feito=bool(item.get("feito")))
                    pl.gravar_item(sheets, sid, folha, item["linha"], novo)
                st.session_state.pop("editando", None)
                st.rerun()
            except ValueError as erro:
                st.warning(str(erro))

        if st.button("Cancelar", key="cancelar_edicao", use_container_width=True):
            st.session_state.pop("editando", None)
            st.rerun()


def _desenhar_item(sheets, sid: str, folha: str, tipo: str, item: dict, gid: int) -> None:
    with st.container(border=True, key=f"linha{item['linha']}"):
        # Botões NA FRENTE do item (pedido de 19/10/2026: no celular fica melhor).
        # `horizontal=True, wrap=False` mantém tudo na mesma linha, sem empilhar.
        with st.container(horizontal=True, vertical_alignment="center",
                          gap="small", wrap=False):
            if st.button("✏️", key=f"e{item['linha']}", help="Editar"):
                st.session_state.pop("apagando", None)
                st.session_state["editando"] = dict(item)
                st.rerun()
            if st.button("🗑️", key=f"a{item['linha']}", help="Apagar"):
                st.session_state.pop("editando", None)
                st.session_state["apagando"] = item["linha"]
                st.rerun()
            if tipo == "consultas":
                if st.button("📷", key=f"f{item['linha']}", help="Anexar foto"):
                    st.session_state.pop("editando", None)
                    st.session_state.pop(f"enviadas{item['linha']}", None)
                    st.session_state["fotografando"] = item["linha"]
                    st.rerun()
            rotulo = item["item"] or item["detalhe"] or "(sem texto)"
            marcado = st.checkbox(
                rotulo, value=item["feito"], width="stretch",
                key=f"m{item['linha']}-{int(item['feito'])}",
            )
        meta = regra.etiqueta(item, tipo)
        if meta:
            st.markdown(f"<span class='meta'>{_escapar(meta)}</span>", unsafe_allow_html=True)
        if tipo == "consultas":
            _area_fotos(sheets, sid, folha, item)

        # Apagar pede confirmação e confere linha+texto antes (regra da casa:
        # apagar é por item, e nunca na linha errada).
        if st.session_state.get("apagando") == item["linha"]:
            st.warning(f"Apagar **{rotulo}**? Não tem como desfazer.")
            c1, c2 = st.columns(2)
            if c1.button("Sim, apagar", key=f"sim{item['linha']}",
                         type="primary", use_container_width=True):
                try:
                    atuais = pl.ler_itens(sheets, sid, folha)
                    regra.conferir(atuais, item["linha"],
                                   item.get("item") or item.get("detalhe"))
                    pl.apagar(sheets, sid, gid, item["linha"])
                except (ValueError, pl.ErroAnotacoes) as erro:
                    st.error(str(erro))
                    st.session_state.pop("apagando", None)
                else:
                    st.session_state.pop("apagando", None)
                    st.rerun()
            if c2.button("Não", key=f"nao{item['linha']}", use_container_width=True):
                st.session_state.pop("apagando", None)
                st.rerun()

        if marcado != item["feito"]:
            pl.marcar(sheets, sid, folha, item["linha"], marcado)
            st.rerun()


def _area_fotos(sheets, sid: str, folha: str, item: dict) -> None:
    """Mostra as fotos já guardadas e, se pedido, o botão de enviar outra."""
    aviso = st.session_state.pop("aviso_fotos", None)
    if aviso and aviso.get("linha") == item["linha"]:
        st.success(aviso["texto"])

    links = regra.fotos_do_item(item)
    if links:
        pedacos = " · ".join(
            f"<a href='{_escapar(url)}' target='_blank'>foto {i + 1}</a>"
            for i, url in enumerate(links)
        )
        st.markdown(f"<span class='meta fotos'>📷 {pedacos}</span>", unsafe_allow_html=True)

    if st.session_state.get("fotografando") != item["linha"]:
        return

    st.caption("O app **reduz a foto** e guarda em **PDF** (fica bem mais leve), na pasta "
               "**PDF e Imagens** do seu Drive.")
    origem = st.radio(
        "De onde vem", ["📸 Câmera", "📁 Arquivo"],
        horizontal=True, key=f"ori{item['linha']}", label_visibility="collapsed",
        help="Câmera abre a câmera do celular; Arquivo deixa escolher da galeria, "
             "dos downloads ou um PDF que já existe.",
    )
    if origem.startswith("📸"):
        # 1080p é o máximo que o `st.camera_input` oferece (as opções são 480p,
        # 720p e 1080p) — sem isso o Streamlit entrega um vídeo mais baixo e o
        # texto do exame borra.
        foto = st.camera_input("Tirar foto", key=f"cam{item['linha']}",
                               resolution="1080p", label_visibility="collapsed")
        st.caption("Câmera da frente? Toque no **⇄** no canto da imagem. "
                   "Para documento, vale mais **📁 Arquivo → Câmera** (foto em "
                   "resolução cheia do celular).")
        arquivos = [foto] if foto else []
    else:
        arquivos = st.file_uploader(
            "Foto do exame / consulta", type=fotos.TIPOS_ACEITOS,
            accept_multiple_files=True, key=f"up{item['linha']}",
            label_visibility="collapsed",
        ) or []
    if not arquivos:
        return

    # Trocar o formato (PDF/JPG) faz a tela rodar de novo COM os mesmos arquivos
    # escolhidos — sem esta trava, a mesma foto subia duas vezes.
    assinaturas = {(a.name, len(a.getvalue())) for a in arquivos}
    marca = f"enviadas{item['linha']}"
    if st.session_state.get(marca) == assinaturas:
        return
    try:
        with st.spinner("Reduzindo e enviando para o Drive..."):
            brutos = [{"nome": getattr(a, "name", "camera.jpg"),
                       "dados": a.getvalue(),
                       "tipo": getattr(a, "type", "")} for a in arquivos]
            prontos = fotos.preparar(brutos)
            novos = []
            for pronto in prontos:
                nome = fotos.nome_do_arquivo(folha, item.get("item"),
                                             item.get("quando"),
                                             sufixo=pronto["sufixo"])
                enviado = fotos.enviar(
                    pronto["dados"], nome, pronto["tipo"], info=_info_oauth(),
                )
                novos.append(enviado["link"])
        pl.gravar_foto(sheets, sid, folha, item["linha"], links + novos)
    except fotos.ErroFotos as erro:
        st.error(str(erro))
    except Exception as erro:                      # noqa: BLE001 (mostrar na tela)
        st.error(f"Não consegui enviar a foto: {erro}")
    else:
        # O `st.rerun()` apaga a mensagem; então ela fica guardada e aparece
        # embaixo do item na rodada seguinte.
        st.session_state[marca] = assinaturas
        st.session_state.pop("fotografando", None)
        antes = sum(len(a.getvalue()) for a in arquivos)
        depois = sum(len(p["dados"]) for p in prontos)
        conta = f"{len(novos)} arquivo(s) guardado(s)"
        if antes and depois < antes:
            conta += f" · {antes / 1024:.0f} KB → {depois / 1024:.0f} KB"
        st.session_state["aviso_fotos"] = {
            "linha": item["linha"],
            "texto": f"{conta} na pasta PDF e Imagens.",
        }
        st.rerun()


def _escapar(texto: str) -> str:
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _limpar_feitos(sheets, sid: str, folha: str, gid: int, feitos: list[dict]) -> None:
    if not st.session_state.get("confirmar_limpeza"):
        if st.button(f"🧹 Limpar os {len(feitos)} feitos", use_container_width=True):
            st.session_state["confirmar_limpeza"] = True
            st.rerun()
        return
    st.warning("Isso apaga de vez os itens marcados. Confirmar?")
    c1, c2 = st.columns(2)
    if c1.button("Sim, apagar", type="primary", use_container_width=True):
        for item in sorted(feitos, key=lambda i: i["linha"], reverse=True):
            pl.apagar(sheets, sid, gid, item["linha"])
        st.session_state.pop("confirmar_limpeza", None)
        st.rerun()
    if c2.button("Não", use_container_width=True):
        st.session_state.pop("confirmar_limpeza", None)
        st.rerun()


def _barra_lateral(sheets, sid: str, folha: str, planilha: dict) -> None:
    with st.sidebar:
        st.markdown("### 📚 Folhas")
        st.caption(f"Planilha: {planilha['name']}")

        with st.form("nova_folha", clear_on_submit=True):
            nome = st.text_input("Nova folha", placeholder="ex.: Filmes, Remédios…")
            tipo_novo = st.selectbox(
                "Tipo", list(regra.TIPOS),
                format_func=lambda t: f"{regra.TIPOS[t]['emoji']} {regra.TIPOS[t]['rotulo']}",
                help="Compras: qtd e preço · Tarefas: prazo e prioridade · Lembretes: data · Lista: só texto",
            )
            criar = st.form_submit_button("Criar folha", use_container_width=True)
        if criar:
            try:
                final = pl.criar_folha_e_anotar(sheets, sid, nome, tipo_novo)
                # pedido para o próximo passo (NÃO escrever em `folha_atual`: o
                # widget das folhas já foi criado nesta rodada)
                st.session_state["folha_pedida"] = final
                st.rerun()
            except ValueError as erro:
                st.warning(str(erro))
            except pl.ErroAnotacoes as erro:
                st.error(str(erro))

        st.divider()
        st.link_button("🔗 Abrir no Google Sheets",
                       f"https://docs.google.com/spreadsheets/d/{sid}/edit",
                       use_container_width=True)
        if st.button("🔄 Recarregar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        with st.expander("ℹ️ Como funciona"):
            st.markdown(
                "- Cada **folha** é uma aba da planilha.\n"
                "- O que você marca aqui vale na planilha (e vice-versa).\n"
                "- **✏️** corrige o item · **🗑️** apaga (só aquele item, e pede confirmação).\n"
                "- **Feitos** ficam guardados: nada some sozinho.\n"
                "- A planilha é o backup: no Drive, *Arquivo → Histórico de versões*.\n"
                "- Para **renomear ou apagar** uma folha, use o Google Sheets (link acima)."
            )
        st.divider()
        if st.button("🔒 Sair", use_container_width=True):
            st.session_state["autorizado"] = False
            st.rerun()


# Qualquer erro na tela é melhor que o "Oh no" genérico do Streamlit Cloud:
# aqui a mensagem aparece escrita, com os detalhes técnicos guardados num
# "detalhes" (foi assim que a gente achou o erro de subida em 19/10/2026).
try:
    principal()
except Exception:
    st.error(
        "**Deu um erro ao abrir o app.** Nada foi perdido — seus dados estão na "
        "planilha, no Drive.\n\nSe você é o Hamilton: abra **Detalhes técnicos** "
        "abaixo e me mande o texto."
    )
    with st.expander("Detalhes técnicos"):
        st.code(traceback.format_exc())
