# Anotações da Raquel

App pessoal de anotações (Streamlit) com senha, guardado numa **planilha do Google
Drive**. Cada folha do app é uma aba da planilha:

| Folha | O que guarda |
|---|---|
| 💰 Vendas e Recebimentos | o que vendeu, quantidade, valor, cliente |
| 🩺 Consultas e Exames | quando, médico/local e **fotos** (vão para uma pasta do Drive) |
| 🔔 Lembretes | o que não pode esquecer |
| 🛒 Compras do mercado | lista de compras com quantidade e preço |
| ✅ Tarefas a fazer | prazo e prioridade |

O app também cria folhas novas (barra lateral → *Nova folha*).

## Como funciona por dentro

- **A planilha é o cofre; o app é a porta.** Nada fica no código: os itens vivem
  numa planilha do Drive.
- Leitura e escrita usam uma **conta de serviço** (o "robô"), que só enxerga o
  que for compartilhado com ela.
- As **fotos** são enviadas com uma **conta de gente** (OAuth), porque conta de
  serviço não pode ser dona de arquivo no Drive. O token fica fora do
  repositório, em `credentials/` (local) ou nos *Secrets* (nuvem).

## Rodar no PC

```bash
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python autorizar-fotos.py          # 1x: autoriza o envio de fotos
./.venv/bin/python -m streamlit run app.py
```

Antes disso, crie `.streamlit/secrets.toml` a partir do modelo
`.streamlit/secrets.toml.example` (senha + `[gcp_service_account]` +
`[google_oauth]`). **Nada disso vai para o git.**

## Testes

```bash
./.venv/bin/python testes.py            # regra, offline (rápido)
./.venv/bin/python testes.py --real ID  # de verdade, numa planilha de teste
```

## Estrutura

| Arquivo | O que é |
|---|---|
| `app.py` | a tela (Streamlit): senha, folhas, lista, editar, apagar, fotos |
| `src/regra.py` | a regra pura: item, "feito", preço, tipo de folha, limites |
| `src/planilha.py` | leitura/escrita na planilha, formatação, colunas |
| `src/fotos.py` | envio de fotos para o Drive (OAuth) |
| `src/acesso.py` | credenciais e clientes do Google |
| `src/config.py` | nome da planilha, escopos, pasta das fotos |
| `testes.py` | testes da regra (+ teste real opcional) |
| `HANDOFF.md` | estado atual, decisões e lições (documentação de trabalho) |

---

> **Nota:** este repositório é a **vitrine pública** do app, espelhada da pasta
> `raquel-anotações/` do repositório privado da casa. A fonte da verdade é a de
> lá; alterações aqui podem ser sobrescritas na próxima sincronização.
