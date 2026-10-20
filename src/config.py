"""Configuração do app Anotações.

Sem Streamlit aqui de propósito: este módulo é importado também pelos testes.
Nada de segredo no código — segredo vem de `.streamlit/secrets.toml` (no PC) ou
dos *Secrets* do Streamlit Cloud.
"""
import os
import socket
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Nome da planilha no Drive. O app procura por este nome entre as planilhas
# compartilhadas com o robô — não precisa colar ID em lugar nenhum.
NOME_PLANILHA = os.getenv("ANOTACOES_PLANILHA", "Anotações da Raquel")

# Planilha de teste (usada pelo testes.py quando é pedido teste de verdade).
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE", str(BASE / "credentials" / "service-account.json")
)

# ------------------------------------------------------------------ fotos
# Pasta do Drive onde as fotos de consultas/exames são guardadas.
PASTA_FOTOS = os.getenv("ANOTACOES_PASTA_FOTOS", "1ZovVMquMgXP3_ldu_iQHfuqp3gazeGJr")

# Token OAuth do DONO (fora do git). O robô não pode subir arquivo: conta de
# serviço não tem cota de Drive ("Service Accounts do not have storage quota").
TOKEN_FOTOS = os.getenv("ANOTACOES_TOKEN_FOTOS", str(BASE / "credentials" / "token-fotos.json"))

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

# Aba escondida que guarda o "tipo" de cada folha (compras/tarefas/lembretes/simples).
# Se ela sumir, o app adivinha pelo nome da folha — nada quebra.
ABA_CONFIG = "_config"

# O que nasce numa planilha nova. (nome da folha, tipo)
# Folhas que nascem junto com a planilha, NA ORDEM EM QUE APARECEM na tela
# (pedido de 20/10/2026). "Vendas" e "Consultas" são as duas que a Raquel usa
# mais: a foto do exame vai na folha de Consultas.
FOLHAS_PADRAO = [
    ("Vendas e Recebimentos", "vendas"),
    ("Consultas e Exames", "consultas"),
    ("Lembretes", "lembretes"),
    ("Compras do mercado", "compras"),
    ("Tarefas a fazer", "tarefas"),
]


def ligar_ipv4() -> None:
    """Força IPv4 nas conexões deste processo.

    Lição nº 24 da casa (18/10/2026): a rede daqui tem IPv6 quebrado — a conexão
    fica pendurada e o Python não tem "Happy Eyeballs" como o Chrome. Sem isto, a
    primeira chamada ao Google pode travar por minutos.
    """
    if os.environ.get("ANOTACOES_IPV4", "1") == "0":
        return
    if getattr(socket, "_anotacoes_ipv4", False):
        return
    original = socket.getaddrinfo

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if family == socket.AF_UNSPEC:
            family = socket.AF_INET
        return original(host, port, family, type, proto, flags)

    socket.getaddrinfo = getaddrinfo  # type: ignore[assignment]
    socket._anotacoes_ipv4 = True  # type: ignore[attr-defined]
