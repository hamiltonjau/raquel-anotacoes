# Anotações da Raquel — instruções

App **pessoal da Raquel** de anotações (Streamlit, porta **8641**), com **senha**,
guardado numa planilha do Google Drive (pasta *Raquel Anotações*).
Pasta: `Documentos/Apps Hamilton/raquel-anotações` — mora dentro do repositório
principal (`hamiltonjau/apps-hamilton`, privado), não tem repositório próprio.

É **cópia** do app `anotacoes/` do Hamilton. **Planilha, senha, porta e serviço
são próprios** — nada é compartilhado com o app dele além do robô.

## Comece lendo
- **`HANDOFF.md`** (nesta pasta) — estado atual, decisões e lições.

## Comandos
- **No dia a dia o app roda como serviço** (systemd de usuário): sobe sozinho ao
  entrar na sessão e **se cair, levanta em 5 s**. Não precisa rodar nada na mão.
  - Estado: `systemctl --user status raquel-anotacoes`
  - Reiniciar (depois de mexer em `src/`): `systemctl --user restart raquel-anotacoes`
  - Log: `journalctl --user -u raquel-anotacoes -n 50 -f`
  - Reinstalar (PC novo/formatação): `bash instalar-servico.sh`
  - ⚠️ **Nunca** `pkill -f app.py` (lição da casa: mata o próprio shell, e ainda
    pode derrubar o app do *Hamilton* junto — os dois rodam `app.py`).
- Rodar na mão, sem serviço (só para depurar; pare o serviço antes, senão a porta
  está ocupada): `./.venv/bin/python -m streamlit run app.py --server.port 8641`
  (ou `bash iniciar-raquel-anotacoes.sh`)
- Testes da regra (offline, rápido): `./.venv/bin/python testes.py`
- Testes de verdade (mexe na planilha da Raquel — limpe depois):
  `./.venv/bin/python testes.py --real <id-da-planilha>`
- Publicar (commit + push no repositório principal, só a pasta `raquel-anotações/`)
  **e** espelhar no repositório público: `./publicar.sh "mensagem"`
- Só o espelho público (é ele que o Streamlit Cloud lê):
  `bash sincronizar-publico.sh "mensagem"`

## Arquivos
| Arquivo | O que é |
|---|---|
| `app.py` | a tela (Streamlit): senha, folhas, lista, editar, apagar |
| `src/regra.py` | **a regra** — pura, sem internet: item, "feito", preço, tipo, limites |
| `src/planilha.py` | conversa com a planilha: ler, escrever, criar folha, formato |
| `src/acesso.py` | credenciais e serviços do Google |
| `src/fotos.py` | **fotos no Drive**: reduz a foto (1800 px), monta o **PDF** e envia com a conta do dono (OAuth), não com o robô |
| `src/config.py` | nome da planilha (**Anotações da Raquel**), escopos, pasta das fotos, `ligar_ipv4()` |
| `autorizar-fotos.py` | roda **1x** (abre o navegador) e cria `credentials/token-fotos.json` |
| `preparar-nuvem.py` | imprime o TOML dos *Secrets* da nuvem (não escreve em arquivo) |
| `testes.py` | testes (regra + opcional de verdade) |
| `raquel-anotacoes.service` | cópia versionada da unidade do systemd (porta 8641) |
| `instalar-servico.sh` | (re)instala a unidade em `~/.config/systemd/user/` |
| `.streamlit/secrets.toml` | **fora do git**: `senha` + `[gcp_service_account]` + `[google_oauth]` |
| `sincronizar-publico.sh` | espelha a pasta em `hamiltonjau/raquel-anotacoes` (público) |

## Como o dado anda
- **Cada folha = uma aba da planilha**, sempre com as mesmas 8 colunas:
  `Feito | Item | Qtd | Preco | Quando | Prioridade | Detalhe | Foto`.
  A **H (Foto)** guarda os links do Drive, um por foto, separados por espaço.
- O **tipo** da folha (compras / vendas / tarefas / lembretes / consultas /
  simples) decide quais campos a tela mostra; ele fica guardado na aba escondida
  **`_config`**. Se a `_config` sumir, o app adivinha pelo nome — nada quebra.
- **A linha manda**: antes de editar/apagar, o app confere `linha + texto`
  (`regra.conferir`). Se não bater (outro aparelho mexeu no meio), recusa em vez
  de escrever na linha errada — mesma lição da página de Ideias.
- **Preço** é número (o Sheets formata em R$); **data** é texto com apóstrofo na
  frente (`'22/10`) para o Sheets não transformar em número de série.
- **Foto** (só na folha de Consultas): o 📷 sobe o arquivo para a pasta
  *PDF e Imagens* do Drive e grava o link na coluna H daquela linha
  (`planilha.gravar_foto`). Quem sobe é **o Hamilton** (OAuth), nunca o robô.
- **Dentro de item, `st.markdown` com HTML usa `<span>`.** `<div>` dentro de
  `st.container(border=True)` colapsa a altura (10 px) no Streamlit 1.66 e o
  texto sobrepõe a linha de baixo. Ver lição 7 do `HANDOFF.md`.

## 🔐 Segurança (não negociável)
- **O app EXIGE SENHA** (`exigir_senha()`, no topo do `app.py`). Mostra
  anotações pessoais. **Não remova a trava.**
- A senha fica em `st.secrets["senha"]` — **nunca** no código, no handoff, no
  LEIA-ME ou em qualquer arquivo que vá pro git.
- No TOML, `senha` tem de ficar **antes** de `[gcp_service_account]` (lição da casa).
- `.env`, `credentials/`, `.streamlit/secrets.toml` **nunca** vão para o git.
- A conta de serviço (robô) é a **mesma** do Controle/Minha Loja/Anotações:
  `loja-robo@loja-estoque-511616.iam.gserviceaccount.com` — só enxerga o que for
  compartilhado com ela.
- **O robô não cria planilha** (conta de serviço não tem Drive). A planilha é
  criada por uma pessoa e compartilhada com o robô como **Editor** — hoje o
  acesso vem pela **pasta** *Raquel Anotações*.
- ⚠️ **Dois apps com `app.py` na mesma máquina**: ao mexer em porta/processo,
  confira a porta (**8640** = Hamilton, **8641** = Raquel) antes de matar nada.
- **O repositório é PÚBLICO** (`hamiltonjau/raquel-anotacoes`, só este app — o
  Streamlit Cloud só deixa **um app privado por workspace**, e o slot é da Loja).
  Consequência: **nada de senha, chave ou token em arquivo versionado** — nem em
  handoff, nem em comentário. Já aconteceu de a senha estar no `HANDOFF.md`
  (20/10/2026); foi removida.
- **`credentials/token-fotos.json` é tão sensível quanto a senha**: dá acesso ao
  Drive inteiro do Hamilton. Fora do git, sempre. Na nuvem vai nos *Secrets*
  (`[google_oauth]`).

## Celular
O app é usado **no celular** (decisão de 20/10). O que existe hoje:
- bloco `@media (max-width: 640px)` no `CSS` do `app.py`: título menor, barra
  fixa do Streamlit respeitada (`padding-top: 3.4rem`), pílulas em **uma linha
  que rola**, botões de ~44 px, campos com 16 px (sem zoom no iPhone), "Deploy"
  escondido, nome do item quebrando em 2 linhas em vez de cortar com "…".
- Para conferir sem celular: Chrome headless com
  `Emulation.setDeviceMetricsOverride` (390×844) e foto de tela — ver
  `HANDOFF.md`, seção "📱 Celular".
- Ainda **não publicado**: enquanto não publicar, celular não abre (é
  `127.0.0.1`). Passo a passo nas *Pendências* do `HANDOFF.md`.

## Regras
- **Nada de limpeza em massa** nas anotações: apagar é por item (linha + texto).
- Mudou o nome da planilha no Drive? Mude `NOME_PLANILHA` em `src/config.py` —
  e **não** deixe igual à do Hamilton (o app acha a planilha **pelo nome**).
- Ao terminar algo importante: `./publicar.sh "mensagem"` + atualizar o `HANDOFF.md`.
- Dúvida de app que apareça em outra aba → registrar no `HANDOFF.md` desta pasta.
