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
TIPOS_ACEITOS = ["jpg", "jpeg", "png", "webp", "heic", "heif", "pdf"]

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


def nome_do_arquivo(folha: str, item: str, quando: str, original: str) -> str:
    """Nome legível dentro da pasta: '2026-10-25 - Dentista - exame.jpg'."""
    from . import regra

    pedacos = [quando or "", item or folha or "foto"]
    base = " - ".join(p for p in pedacos if p)
    base = regra.limpar(base, 90).replace("/", "-").replace("\\", "-")
    sufixo = Path(str(original or "")).suffix.lower() or ".jpg"
    return f"{base}{sufixo}"


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
