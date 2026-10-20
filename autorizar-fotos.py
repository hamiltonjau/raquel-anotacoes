"""Autoriza o app a ENVIAR fotos para o Drive do Hamilton (uma vez só).

Por que existe: conta de serviço (o "robô") não pode ser dona de arquivo —
`files.create` devolve 403 "storage quota exceeded". Quem sobe foto é gente.
Então o app usa o SEU login (OAuth), com um token guardado fora do git.

Rode no PC, na pasta do app:

    ./.venv/bin/python autorizar-fotos.py

Ele abre o navegador na tela do Google; escolha a conta hamiltonjau@gmail.com e
clique em "Permitir". O token fica em credentials/token-fotos.json (fora do git).

⚠️ O escopo é `drive` (Drive inteiro): é o único jeito de gravar DENTRO de uma
pasta que já existe (o escopo `drive.file` só enxerga o que o próprio app criou).
"""
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BASE = Path(__file__).resolve().parent
CLIENTE = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    BASE.parent / "raquel-modas" / "loja-sheets-api" / "credentials" / "client_secret.json"
)
SAIDA = BASE / "credentials" / "token-fotos.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

if SAIDA.exists():
    atual = Credentials.from_authorized_user_info(json.loads(SAIDA.read_text()))
    if set(SCOPES) <= set(atual.scopes or []):
        if not atual.valid:
            atual.refresh(Request())
        SAIDA.write_text(atual.to_json(), encoding="utf-8")
        print(f"✓ Já autorizado ({SAIDA}). Nada a fazer.")
        print("  conta:", json.loads(SAIDA.read_text()).get("account", "(não anotada)"))
        raise SystemExit(0)
    print("· O token atual não tem o escopo `drive` — vou pedir de novo.")

if not CLIENTE.exists():
    print(f"✗ Não achei o client_secret.json em {CLIENTE}")
    raise SystemExit(1)

fluxo = InstalledAppFlow.from_client_secrets_file(str(CLIENTE), scopes=SCOPES)
print("· Abrindo o navegador para você permitir o acesso ao Drive...")
credenciais = fluxo.run_local_server(port=0, access_type="offline",
                                     prompt="consent", open_browser=True)

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text(credenciais.to_json(), encoding="utf-8")
SAIDA.chmod(0o600)

print(f"✓ Token salvo em {SAIDA}")
print("  escopos:", credenciais.scopes)
if not credenciais.refresh_token:
    print("!! Sem refresh_token — o token vai morrer em 1 hora. Rode de novo.")
    raise SystemExit(1)
print("  (tem refresh_token: sim)")
