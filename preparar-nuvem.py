"""Monta o bloco dos *Secrets* para o Streamlit Cloud (nuvem).

Não escreve em lugar nenhum do git: só imprime na tela o TOML pronto para você
**copiar e colar** em *Settings > Secrets* do app no share.streamlit.io.

Ele junta três coisas que já estão no PC:
  - `senha` (de `.streamlit/secrets.toml`)
  - `[gcp_service_account]` (o robô, idem)
  - `[google_oauth]` (o token do dono, de `credentials/token-fotos.json`)

Rode na pasta do app:

    ./.venv/bin/python preparar-nuvem.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SEGREDOS = BASE / ".streamlit" / "secrets.toml"
TOKEN = BASE / "credentials" / "token-fotos.json"


def _texto(valor) -> str:
    """Valor como string TOML (aspas duplas, com escape do que precisa)."""
    return '"' + str(valor).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    if not SEGREDOS.exists():
        raise SystemExit(f"✗ Não achei {SEGREDOS}")

    conteudo = SEGREDOS.read_text(encoding="utf-8").rstrip()
    # Do arquivo local, tudo serve menos o que for do token das fotos (que ainda
    # não existe lá). Se já houver um bloco [google_oauth], ele é descartado —
    # o token bom é o do arquivo JSON, que se renova sozinho.
    corte = conteudo.find("[google_oauth]")
    if corte != -1:
        conteudo = conteudo[:corte].rstrip()

    print("# ---- cole isto em Settings > Secrets (share.streamlit.io) ----")
    print(conteudo)
    print()

    if TOKEN.exists():
        dados = json.loads(TOKEN.read_text(encoding="utf-8"))
        print("[google_oauth]")
        for chave in ("refresh_token", "token", "token_uri", "client_id", "client_secret"):
            if dados.get(chave):
                print(f"{chave} = {_texto(dados[chave])}")
        escopos = dados.get("scopes") or ["https://www.googleapis.com/auth/drive"]
        print("scopes = [" + ", ".join(_texto(e) for e in escopos) + "]")
    else:
        print("# ⚠️ Sem credentials/token-fotos.json — rode antes:")
        print("#    ./.venv/bin/python autorizar-fotos.py")
    print("# ---- fim ----")


if __name__ == "__main__":
    main()
