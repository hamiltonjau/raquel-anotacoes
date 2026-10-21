"""Fotos das consultas/exames no Google Drive — enviadas com a conta do DONO.

Por que não é o robô: conta de serviço **não pode ser dona de arquivo**
(`files.create` devolve 403 "Service Accounts do not have storage quota"), então
quem sobe a foto é a conta do Hamilton, por OAuth. O token fica em
`credentials/token-fotos.json` (fora do git) no PC e, publicado, nos *Secrets* do
Streamlit Cloud, na chave `google_oauth` (o conteúdo do arquivo, em TOML).

Nada de Streamlit aqui: quem chama passa o `info` (dicionário do token) quando vem
dos *Secrets*; sem `info`, lemos o arquivo local.
"""
import io
import json
import threading
from pathlib import Path

from .config import PASTA_FOTOS, TOKEN_FOTOS, ligar_ipv4

SCOPES = ["https://www.googleapis.com/auth/drive"]

# `heic` fica FORA de propósito: se o celular manda HEIC cru, o Pillow não abre
# sem uma biblioteca extra. Sem a extensão na lista, o iPhone converte a foto
# para JPEG antes de enviar (e aí tudo funciona em qualquer máquina).
TIPOS_ACEITOS = ["jpg", "jpeg", "png", "webp", "pdf"]

# O que deixa a foto leve não é o PDF: é reduzir o lado e recomprimir. 1800 px
# dá para ler exame no celular e cabe em ~200-400 KB.
LADO_MAX = 1800
QUALIDADE = 78

_trava = threading.Lock()
_cache = {"chave": None, "creds": None}


class ErroFotos(Exception):
    """Falha ao falar com o Drive sobre fotos (mensagem já em português)."""


def _dados_do_token(info: dict | None) -> dict:
    if info:
        return dict(info)
    caminho = Path(TOKEN_FOTOS)
    if not caminho.exists():
        raise ErroFotos(
            "Ainda não autorizei o envio de fotos.\n\n"
            "No PC, rode uma vez:  `./.venv/bin/python autorizar-fotos.py`\n"
            "Na nuvem, cole o conteúdo de `credentials/token-fotos.json` nos "
            "*Secrets*, na chave `google_oauth`."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def credenciais(info: dict | None = None):
    """Credenciais OAuth do dono, prontas para usar (renova sozinho)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    dados = _dados_do_token(info)
    chave = dados.get("refresh_token") or dados.get("token") or ""
    with _trava:
        if _cache["chave"] != chave:
            _cache.update(chave=chave, creds=Credentials.from_authorized_user_info(
                dados, scopes=dados.get("scopes") or SCOPES))
        creds = _cache["creds"]
        if not creds.valid:
            creds.refresh(Request())
            # Guarda o token novo no arquivo (se estivermos no PC). Na nuvem o
            # token vive só na memória e renova de novo quando precisar.
            if not info:
                try:
                    Path(TOKEN_FOTOS).write_text(creds.to_json(), encoding="utf-8")
                except OSError:
                    pass
        return creds


def servico(info: dict | None = None):
    """Cliente do Drive da conta do dono."""
    from googleapiclient.discovery import build

    ligar_ipv4()
    return build("drive", "v3", credentials=credenciais(info), cache_discovery=False)


def nome_do_arquivo(folha: str, item: str, quando: str, original: str = "",
                    sufixo: str | None = None) -> str:
    """Nome legível dentro da pasta: '25/10/2026 - Dentista.pdf'."""
    from . import regra

    pedacos = [quando or "", item or folha or "foto"]
    base = " - ".join(p for p in pedacos if p)
    base = regra.limpar(base, 90).replace("/", "-").replace("\\", "-")
    ext = sufixo or Path(str(original or "")).suffix.lower() or ".jpg"
    return f"{base}{ext}"


def _abrir_foto(dados: bytes, lado_max: int = LADO_MAX):
    """Abre a imagem do celular já endireitada (EXIF) e reduzida."""
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(dados))
    img.load()
    img = ImageOps.exif_transpose(img)          # senão a foto sai deitada
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((lado_max, lado_max), Image.LANCZOS)
    return img


def preparar(arquivos: list[dict], como_pdf: bool = True,
             lado_max: int = LADO_MAX, qualidade: int = QUALIDADE) -> list[dict]:
    """Deixa os arquivos do celular prontos para subir, do menor jeito.

    `arquivos`: `[{"nome": ..., "dados": b"...", "tipo": "image/jpeg"}]`.

    Devolve `[{"dados", "tipo", "sufixo", "paginas"}]`:

    - **PDF** que já veio do celular: passa reto (não mexe em PDF de verdade).
    - **Imagem** com `como_pdf=True`: todas viram **um único PDF** (a foto de um
      exame de 3 folhas fica num arquivo só).
    - **Imagem** com `como_pdf=False`: um **JPG** por foto, já reduzido.

    ⚠️ O que diminui de verdade é reduzir/recomprimir (1800 px, qualidade 78):
    uma foto de 4 MB vira ~300 KB. O PDF é só a embalagem — ele não encolhe a
    foto sozinho.
    """
    saida: list[dict] = []
    imagens = []                                # (nome, PIL.Image)
    try:
        for arquivo in arquivos or []:
            nome = str(arquivo.get("nome") or "")
            tipo = str(arquivo.get("tipo") or "").lower()
            dados = arquivo.get("dados") or b""
            if tipo == "application/pdf" or nome.lower().endswith(".pdf"):
                saida.append({"dados": dados, "tipo": "application/pdf",
                              "sufixo": ".pdf", "paginas": 1})
                continue
            imagens.append((nome, _abrir_foto(dados, lado_max)))

        if not imagens:
            return saida

        if como_pdf:
            buffer = io.BytesIO()
            primeira = imagens[0][1]
            resto = [imagem for _, imagem in imagens[1:]]
            primeira.save(buffer, "PDF", save_all=True, append_images=resto,
                          resolution=150.0, quality=qualidade)
            saida.append({"dados": buffer.getvalue(), "tipo": "application/pdf",
                          "sufixo": ".pdf", "paginas": len(imagens)})
        else:
            for _, imagem in imagens:
                buffer = io.BytesIO()
                imagem.save(buffer, "JPEG", quality=qualidade, optimize=True)
                saida.append({"dados": buffer.getvalue(), "tipo": "image/jpeg",
                              "sufixo": ".jpg", "paginas": 1})
        return saida
    finally:
        for _, imagem in imagens:
            try:
                imagem.close()
            except Exception:                   # noqa: BLE001 (não interessa)
                pass


def enviar(dados: bytes, nome: str, mimetype: str, info: dict | None = None,
           pasta: str | None = None) -> dict:
    """Sobe a foto para a pasta e devolve {'id', 'link', 'nome'}."""
    from googleapiclient.http import MediaIoBaseUpload

    drive = servico(info)
    corpo = {"name": nome, "parents": [pasta or PASTA_FOTOS]}
    midia = MediaIoBaseUpload(io.BytesIO(dados), mimetype=mimetype or "application/octet-stream",
                              resumable=False)
    try:
        criado = drive.files().create(
            body=corpo, media_body=midia,
            fields="id,name,webViewLink,mimeType,size",
        ).execute()
    except Exception as erro:                       # noqa: BLE001 (mensagem clara)
        raise ErroFotos(f"Não consegui enviar a foto para o Drive: {erro}") from erro
    return {"id": criado["id"], "link": criado.get("webViewLink", ""),
            "nome": criado.get("name", nome)}


def deletar(file_id: str, info: dict | None = None) -> None:
    """Apaga uma foto (usado nos testes; o app não apaga sozinho)."""
    servico(info).files().delete(fileId=file_id).execute()
