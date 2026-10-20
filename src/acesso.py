"""Acesso ao Google: credenciais e os dois serviços que o app usa.

Nada de Streamlit aqui — o app passa as credenciais (segredos) e este módulo só
constrói os clientes. Assim os testes conseguem usar as mesmas funções.

⚠️ **Regra que nasceu de um crash (20/10/2026):** os CLIENTES (`sheets`/`drive`,
que carregam um `httplib2.Http`) **não podem ser compartilhados entre threads**.
A própria httplib2 avisa: *"Not thread-safe, requires external synchronization"*.
O Streamlit roda cada rodada numa thread e, com dois cliques rápidos (ou duas
abas), duas rodadas se cruzam. Compartilhar o cliente corrompeu a memória e o
processo abortou com `free(): corrupted unsorted chunks` (core dump).
Por isso: **credenciais** ficam em cache (são caras e só se leem), **clientes**
são criados a cada rodada, um por thread.
"""
import threading

from .config import SCOPES, SERVICE_ACCOUNT_FILE, ligar_ipv4

# A credencial é lida uma vez e reaproveitada (evita uma troca de token por
# rodada). O `creds` é devolvido a quem pediu e cada um monta o seu cliente.
_trava = threading.Lock()
_cache = {"chave": None, "creds": None}


def _chave(info: dict | None, arquivo: str | None):
    if info:
        return ("info", str(info.get("client_email", "")),
                str(info.get("private_key_id", "")))
    return ("arquivo", arquivo or SERVICE_ACCOUNT_FILE)


def credenciais(info: dict | None = None, arquivo: str | None = None):
    """Devolve as credenciais da conta de serviço (em cache, com trava)."""
    from google.oauth2 import service_account

    chave = _chave(info, arquivo)
    with _trava:
        if _cache["chave"] != chave:
            if info:
                novas = service_account.Credentials.from_service_account_info(
                    info, scopes=SCOPES
                )
            else:
                novas = service_account.Credentials.from_service_account_file(
                    arquivo or SERVICE_ACCOUNT_FILE, scopes=SCOPES
                )
            _cache.update(chave=chave, creds=novas)
        return _cache["creds"]


def servicos(info: dict | None = None, arquivo: str | None = None):
    """Devolve (sheets, drive) autenticados — clientes NOVOS a cada chamada.

    `info` = dicionário `[gcp_service_account]` (Streamlit Cloud).
    `arquivo` = caminho do JSON (no PC, `credentials/service-account.json`).
    """
    ligar_ipv4()          # antes de qualquer conexão (lição nº 24 da casa)
    from googleapiclient.discovery import build

    creds = credenciais(info=info, arquivo=arquivo)
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    return sheets, drive
