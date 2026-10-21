# Anotações da Raquel — handoff (estado atual)

> Criado em **20/10/2026**, na sessão da aba **raquel-anotacoes**, como cópia do
> app `anotacoes/` do Hamilton — mas com **planilha própria, senha própria,
> porta própria e serviço próprio**.

## O que é
App **pessoal da Raquel** de anotações, com senha, no padrão da casa (Streamlit).
O dado mora numa **planilha do Drive** dela (folha = aba da planilha).

| Peça | Onde |
|---|---|
| Pasta | `~/Documentos/Apps Hamilton/raquel-anotações` |
| Porta | **8641** (só `127.0.0.1`) |
| Serviço | `raquel-anotacoes.service` (systemd de usuário) |
| Planilha | **Anotações da Raquel** |
| ID da planilha | `1dKk9vxDVjbTTh4X4GujoEqpFPijBnO6UDDEXPHPB6Tk` |
| Pasta no Drive | **Raquel Anotações** — `1PsAJAPxTVbsPFTf_oHu2jj-WKZzgrIer` |
| Dono da planilha | `hamiltonjau@gmail.com` (o robô só é Editor) |
| Robô | `loja-robo@loja-estoque-511616.iam.gserviceaccount.com` |
| Cartão na Central | id `raquel-anotacoes`, emoji 🗒️ |
| Repositório **público** | `hamiltonjau/raquel-anotacoes` (só este app — é o que o Streamlit Cloud lê) |
| Pasta das **fotos** | **PDF e Imagens** — `1ZovVMquMgXP3_ldu_iQHfuqp3gazeGJr` |
| Token das fotos (OAuth) | `credentials/token-fotos.json` (fora do git) |

**Link da planilha:**
https://docs.google.com/spreadsheets/d/1dKk9vxDVjbTTh4X4GujoEqpFPijBnO6UDDEXPHPB6Tk/edit

## 🔐 A senha
- **6 dígitos**, escolhida pelo Hamilton em 20/10/2026. **Não fica escrita em
  arquivo versionado** (regra do `AGENTS.md`): está no `secrets.toml` do PC e,
  na nuvem, nos *Secrets*. Para trocar, edite o TOML e reinicie o serviço.
- Não existe em nenhum arquivo versionado: fica em
  `raquel-anotações/.streamlit/secrets.toml` (fora do git). No TOML, `senha`
  **antes** de `[gcp_service_account]`.
- **É outra senha**, diferente da do app do Hamilton (lá é `687482`) e da Loja.
- Não há cadastro nem limite de tentativas: senha aqui é **uma linha de arquivo**.
  Para trocar: editar o TOML e **reiniciar o serviço**.

## Estado: pronto e no ar
| Peça | Situação |
|---|---|
| Planilha | ✅ criada **à mão** pelo Hamilton dentro da pasta *Raquel Anotações* |
| Estrutura | ✅ 5 folhas (3 padrão + **Vendas e Recebimentos** + **Consultas e Exames**) e `_config` |
| Tela | ✅ título **"📝 Anotações da Raquel"**, legenda "Guardado em Anotações da Raquel" |
| Senha | ✅ testada **na tela**: a senha antiga é recusada, a atual entra |
| Fotos nas consultas | ✅ **câmera ou arquivo**, foto reduzida a 1800 px e guardada em **PDF**, com a conta do Hamilton (OAuth), na pasta *PDF e Imagens* |
| Celular | ✅ tema/medidas de celular prontos (conferidos em tela de 390 px) |
| Testes | ✅ `./.venv/bin/python testes.py` → **100/100**; `--real <id>` → **110**, só falha *"preparou a planilha"* (esperada, ver abaixo) |
| Serviço | ✅ instalado e ativo (`systemctl --user status raquel-anotacoes`) |
| Central | ✅ cartão 🗒️ registrado em `central/config.json` |
| Publicar na internet | ✅ **no ar**: https://raquel-anotacoes.streamlit.app (repo público `hamiltonjau/raquel-anotacoes`, ver abaixo) |

## Como rodar / testar
```bash
cd ~/Documentos/Apps\ Hamilton/raquel-anotações
./.venv/bin/python -m streamlit run app.py --server.port 8641   # na mão
bash iniciar-raquel-anotacoes.sh                                # ou pelo serviço
./.venv/bin/python testes.py                                    # regra (offline)
./.venv/bin/python testes.py --real <id>                        # mexe no Google de verdade
./.venv/bin/python autorizar-fotos.py                           # 1x: deixa o app enviar foto (abre o navegador)
./.venv/bin/python preparar-nuvem.py                            # monta os Secrets da nuvem (só imprime na tela)
bash instalar-servico.sh                                        # (re)instala o serviço
./publicar.sh "mensagem"                                        # commit + push (repo raiz) + espelho público
bash sincronizar-publico.sh "mensagem"                          # só o espelho público (Streamlit Cloud)
```
⚠️ **Streamlit não recarrega `src/`**: mudou código, `systemctl --user restart
raquel-anotacoes`.

## O que foi feito em 20/10/2026 (a cópia)
1. `rsync` de `anotacoes/` para `raquel-anotações/` **sem** `.venv` e
   `__pycache__`; venv nova criada do `requirements.txt`
   (**streamlit 1.66.0**, **pyarrow 24.0.0**).
2. `src/config.py`: `NOME_PLANILHA = "Anotações da Raquel"`.
3. `app.py`: título da aba e cabeçalhos → "Anotações da Raquel".
4. `.streamlit/secrets.toml`: senha própria (6 dígitos).
5. Arquivos renomeados: `anotacoes.service` → `raquel-anotacoes.service`,
   `iniciar-anotacoes.sh` → `iniciar-raquel-anotacoes.sh`; porta 8640 → **8641**
   em tudo (`--server.port`, `PORTE`, `RAQUEL_ANOTACOES_PORTA`).
6. `central/config.json`: cartão **🗒️ Anotações da Raquel**.
7. Serviço instalado (`bash instalar-servico.sh`) e conferido: HTTP 200.

## Provas desta sessão
- **`garantir_estrutura`** na planilha nova → *"Preparei as 5 folhas"*
  (era 3; em 20/10 virou 5 — Vendas e Recebimentos e Consultas e Exames passaram
  a nascer junto, ver `FOLHAS_PADRAO` em `src/config.py`).
- **`achar_planilha('Anotações da Raquel')`** devolve **o ID certo** — e não a
  planilha do Hamilton (nomes diferentes de propósito, ver lição 1).
- **Teste real** (`testes.py --real <id>`): 110 verificações, 1 falha esperada —
  adicionar, ler, preço
  `18,90`, data `05/11/2026`, marcar feito, editar sem perder o "feito",
  apagar linha, criar folha, recusar nome repetido. A "falha" foi
  *"preparou a planilha"*, que espera a planilha **crua** e eu já tinha
  preparado antes (o app devolveu `''` = nada a fazer). **Não é bug.**
- **Limpeza conferida**: folha `Filmes` do teste apagada, `_config` sem resíduo,
  linhas zeradas → 5 folhas com 0 itens.
- **Tela, medida no navegador**: senha velha recusada (`Senha incorreta.`), senha
  nova entra, aparece *"Guardado em Anotações da Raquel, no seu Drive"*.

## Decisões (e por quê)
- **Nome diferente do app do Hamilton** ("Anotações" × "Anotações da Raquel"):
  `achar_planilha` procura **pelo nome** entre as planilhas compartilhadas com o
  robô. Nome igual = risco de um app abrir a planilha do outro.
- **Planilha dentro da pasta *Raquel Anotações***: pedido do Hamilton (20/10) —
  o dado dela fica separado do resto.
- **Serviço próprio** (não sobe junto com o do Hamilton): cada app tem sua
  unidade, seu log e sua porta.
- Todo o resto do desenho (colunas fixas, `_config`, "a linha manda", data como
  texto, preço como número, sem "caixinha" na coluna inteira) é o mesmo do app
  original — **não reinventar**.

## Lições (repetidas de propósito)
1. **Conta de serviço não tem Drive.** `files.create` dá
   **403 "The user's Drive storage quota has been exceeded."** (a mensagem é
   enganosa: o robô não tem quota **nenhuma**). Quem cria planilha é gente.
   O robô só lê e escreve no que for compartilhado.
2. **Compartilhar a pasta resolve.** Depois que o Hamilton compartilhou *Raquel
   Anotações* com o robô (Editor), o robô enxergou a pasta e a planilha dentro
   dela — **sem** compartilhar arquivo por arquivo.
3. **Pasta errada = 404, não 403.** Sem permissão, o Drive responde
   *"File not found"* — não dá para distinguir "não existe" de "não tenho acesso".
4. **O robô não pode ser dono do arquivo.** A planilha é do `hamiltonjau@gmail.com`
   e o robô entra por compartilhamento — é assim que o dado sobrevive.
5. Lições profundas do app original (caixinha/`FALSE`, `append` fora de lugar,
   `DimensionRange`, `st.session_state` de widget, segfault do `pyarrow` 26):
   estão no `HANDOFF.md` de `anotacoes/` — **vale ler antes de mexer no código**.
6. **Conta de serviço não pode ser dona de arquivo.** `files.create` com o robô
   dá **403 "Service Accounts do not have storage quota"**. Para **enviar**
   arquivo (foto) só serve **OAuth de gente**: `autorizar-fotos.py` →
   `credentials/token-fotos.json`. E o escopo tem de ser `drive`, porque
   `drive.file` **não enxerga** pasta que já existe (deu 404 na pasta
   *PDF e Imagens*, mesmo estando compartilhada com o robô).
7. **`<div>` dentro de `st.container(border=True)` colapsa no Streamlit 1.66.**
   Medido: `st.markdown("<div>x</div>")` → **10 px** de altura (o texto vaza e
   sobrepõe a linha de baixo); com **`<span>`** → **26 px**, certo. Foi assim que
   a linha "22/10/2026 · Laboratório" ficou **em cima** do "📷 foto 1" no
   celular. Regra da casa: **dentro de item, `st.markdown` com HTML usa
   `<span>`**, nunca `<div>`.
8. **O componente das pílulas não se chama `stPills`.** No DOM é
   `[data-testid="stButtonGroup"]` (com `div[role="radiogroup"]` dentro), e é
   nesse `div` que mora o `flex-wrap: wrap` que quebrava as 5 folhas em 3 linhas.
9. **A barra do Streamlit é fixa e cobre o conteúdo.** Com
   `.block-container { padding-top: .5rem }` o `h2` do título ficou **atrás**
   dela (topo 18 px). No celular, **3,4rem** em cima. E cuidado: a altura de um
   elemento **não** prova que ele aparece — o DOM dizia "visível" e o print não
   mostrava nada.
10. **`pkill -f _celular_teste.py` mata o próprio comando** (o padrão casa com a
   linha de comando do shell que o executa). Para parar um app de teste, ache o
   PID pela **porta**: `ss -ltnp | grep :8699`. (A lição nº 27 da casa já dizia
   isso para `app.py` — vale para qualquer padrão.)
11. **Campo controlado do React não aceita `input.value = ...`.** No navegador
   headless (Streamlit 1.66), o jeito que funciona é o *setter* nativo:
   `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, txt)`
   + `dispatchEvent(new Event('input', {bubbles: true}))`. E `.click()` puro às
   vezes não dispara o `st.button`: o que passou foi a sequência completa de
   `pointerdown/mousedown/pointerup/mouseup/click` nas coordenadas do botão.
12. **`st.camera_input` sem `resolution` captura no tamanho do widget.** O padrão
   (`None`) tira a foto com a largura em que o vídeo aparece na tela — no celular,
   **~350 px**. A imagem nasce borrada e não tem compressão que conserte. Passe
   `resolution="1080p"` (as opções são 480p, 720p e 1080p; o 1080p vira
   `minScreenshotWidth = 1920`). Descoberto em 21/10/2026 com o print de um
   comprovante ilegível.
13. **"PDF é menor" não é verdade sozinho — quem encolhe é a redução.** Guardar
   como PDF só embala a foto; 4 MB de foto continuam ~4 MB dentro do PDF. O ganho
   vem de `thumbnail(1800)` + JPEG q78. E, se a foto já vier muito comprimida, o
   PDF pode sair **maior** que o original — por isso o aviso na tela só mostra
   `antes → depois` quando o depois é menor.

## Folhas (20/10/2026, a pedido dele)
Além das 3 padrão, duas folhas novas com **tipo próprio** (o tipo decide os
campos e o visual da planilha):

| Folha | Tipo | Campos | Emoji |
|---|---|---|---|
| Vendas e Recebimentos | `vendas` (novo) | Qtd · **Valor** · Cliente / obs. | 💰 |
| Consultas e Exames | `consultas` (novo) | Quando · Médico / local | 🩺 |

Os tipos `vendas` e `consultas` foram **acrescentados** em `src/regra.py`
(`TIPOS`) — `vendas` é o formato de conta das compras (qtd + valor, coluna em R$
no Sheets) e `consultas` é o dos lembretes (data + texto). Também entraram as
`palavras` de reconhecimento por nome (`venda`, `recebimento`, `consulta`,
`exame`), então **mesmo que a `_config` se perca** o app continua acertando o
tipo pelo nome da folha (era o furo: sem palavra-chave, caía em "simples" e a
folha perdia Qtd/Valor — aconteceu aqui na primeira hora).

## 📷 Fotos nas consultas (20/10/2026)

Pedido do Hamilton: **guardar a foto do exame/consulta junto do item**, na pasta
*PDF e Imagens* do Drive (`1ZovVMquMgXP3_ldu_iQHfuqp3gazeGJr`).

**Como funciona hoje**
- Só na folha de **Consultas e Exames** aparece o botão **📷** em cada item.
- Ele abre duas escolhas: **📸 Câmera** (abre a câmera do celular, `st.camera_input`)
  ou **📁 Arquivo** (`st.file_uploader`: várias fotos de uma vez — jpg, jpeg, png,
  webp — ou um PDF que já existe).
- **Toda foto é reduzida e vira PDF antes de subir** (pedido do Hamilton em
  21/10: "foto da câmera, guardado como PDF, que é menor"). Vários arquivos
  escolhidos de uma vez viram **um único PDF com N páginas**.
- O app sobe para o Drive e grava o link na **coluna H ("Foto")** da linha.
- O item passa a mostrar **📷 foto 1 · foto 2**, que abre no Drive.

**O tamanho menor vem de reduzir, não do PDF** (lição 12): a foto é endireitada
pelo EXIF e reduzida a **2600 px** no lado maior, JPEG qualidade 88 (`LADO_MAX` e
`QUALIDADE` em `src/fotos.py`). O aviso na tela mostra `518 KB → 120 KB` quando é
possível comparar — se o PDF ficar maior (foto já muito comprimida), ele **não**
mostra a conta.

**Qualidade (conserto de 21/10, à noite).** O Hamilton mandou o print de um
comprovante **ilegível**. A causa não era o JPEG nem o PDF: **era o
`st.camera_input` sem `resolution`** — sem esse parâmetro o Streamlit captura uma
imagem do **tamanho em que o vídeo aparece na tela** (num celular, ~350 px de
largura!). A foto nascia borrada e nenhuma compressão depois salva.

O que mudou:

| Antes | Agora |
|---|---|
| `st.camera_input` sem resolução → print da tela (~350 px) | `resolution="1080p"` (o máximo que existe: 480p, 720p, 1080p) |
| 1800 px / q78 | 2600 px / q88 |

Com isso a foto da câmera não é mais reduzida (1920 < 2600) — só reencodada.
Documento de 12 MP vindo de *Arquivo* cai para 2600 px (~600-900 KB). Legenda
embaixo da câmera lembra que o **⇄** troca para a câmera de trás (o padrão é a da
frente) e que, para documento, **📁 Arquivo → Câmera** dá a resolução cheia do
celular (12 MP, muito melhor que o vídeo de 1080p).

**HEIC ficou fora da lista de propósito:** sem a extensão em `TIPOS_ACEITOS`, o
iPhone converte a foto para JPEG antes de mandar; se aceitasse HEIC, o Pillow não
abriria sem `pillow-heif` (dependência a mais na nuvem).

⚠️ **Trava de reenvio:** trocar a escolha (Câmera ↔ Arquivo) faz a tela rodar de
novo **com o mesmo arquivo já escolhido**. Sem a trava (`session_state["enviadas<linha>"]`)
a mesma foto subiria duas vezes. A trava é limpa quando o 📷 é clicado de novo.

**Quem sobe a foto é o Hamilton, não o robô.** (Decisão dele em 20/10: "o app
envia, usando sua conta".) O motivo está na lição 6: conta de serviço **não pode
ser dona de arquivo**. Então:

| Peça | O que é |
|---|---|
| `autorizar-fotos.py` | pede a permissão **uma vez** (abre o navegador, você clica em *Permitir*) |
| `credentials/token-fotos.json` | o token que sobra (fora do git); **renova sozinho** |
| `src/fotos.py` | `preparar()` (reduz + PDF) / `enviar()` / `deletar()` / `nome_do_arquivo()` |
| `src/config.py` | `PASTA_FOTOS` e `TOKEN_FOTOS` |
| `src/planilha.py` | `gravar_foto()` escreve **só a célula H** daquela linha |

**Escopo:** `https://www.googleapis.com/auth/drive` (o Drive inteiro). É o único
jeito de gravar **dentro de uma pasta que já existe** — o escopo `drive.file` só
enxerga arquivo que o próprio app criou (testado: com `drive.file` a pasta dá
**404**). O token é do dono, fica no PC, e na nuvem vai para os *Secrets*
(`[google_oauth]`).

**Nome do arquivo no Drive:** `AAAA-MM-DD - Item.ext` (ex.:
`22-10-2026 - Hemograma.png`) — a barra da data vira hífen.

**Prova (20/10):** item "Hemograma" criado na tela, 📷 clicado, PNG enviado pelo
navegador → a planilha ficou com o link em `H2` e o Drive com
`22-10-2026 - Hemograma.png`, dono `hamiltonjau@gmail.com`. Item e foto
**apagados** depois; a pasta ficou vazia de novo.
Também testado o caminho **da nuvem** (token vindo de dicionário, sem arquivo):
subiu e apagou igual.

**Prova (21/10, câmera + PDF):** no app rodando (8641), entrei, abri a folha
*Consultas e Exames*, criei "Teste foto PDF" e cliquei no 📷 → apareceram
**📸 Câmera** (o navegador pediu a câmera: *"This app would like to use your
camera"*) e **📁 Arquivo**. Enviei um JPG de **518 KB** por *Arquivo* → a planilha
ficou com o link em `H3` e o Drive com `21-10-2026 - Teste foto PDF.pdf`
(**795 KB**, `application/pdf`). Item apagado pela tela e arquivo apagado do
Drive; a pasta ficou vazia.

**Prova (21/10, no app publicado):** o mesmo teste em
https://raquel-anotacoes.streamlit.app — entrei com a senha, criei "Teste nuvem
PDF", 📷 → **📁 Arquivo**, enviei um JPG de **137 KB** → `H3` ganhou o link e o
Drive ficou com `21-10-2026 - Teste nuvem PDF.pdf` (**102 KB**,
`application/pdf`, dono `hamiltonjau@gmail.com`). Ou seja: **o Pillow funciona na
nuvem** (a foto foi reduzida e virou PDF lá). Item apagado pela tela e arquivo
apagado do Drive; pasta vazia. A opção **📸 Câmera** apareceu nos dois (no PC o
navegador pediu permissão de câmera — no celular é a câmera de trás).

## 🌐 O repositório público (por que existe)

O **Streamlit Community Cloud** aceita **um único app privado por workspace** — e
esse slot já é da **Minha Loja**. Tentativa em 20/10/2026:

> *"You can only have one private app per workspace on Community Cloud"*

Apps de repositório **público** não têm esse limite. Decisão do Hamilton:
**repositório público só com este app** — e não o `apps-hamilton` inteiro, que
tem os handoffs de todos os apps (com senhas e e-mails anotados).

| Peça | Onde |
|---|---|
| Fonte da verdade | esta pasta, no repositório **privado** `apps-hamilton` |
| Vitrine pública | `hamiltonjau/raquel-anotacoes` (raiz = esta pasta) |
| Cópia local do espelho | `~/Documentos/raquel-anotacoes-publico` |

**Como sincroniza:** `./publicar.sh "msg"` faz o commit aqui **e** roda
`bash sincronizar-publico.sh "msg"` no fim (se o espelho falhar, o commit daqui
já está feito — é só rodar o sincronizador de novo).

O `sincronizar-publico.sh` usa `rsync --delete` com exclusões: **nunca** vão para
o público `.venv/`, `credentials/`, `.streamlit/secrets.toml`, a unit do systemd,
os scripts locais e o `README.md` (que só existe no público). ⚠️ O
`--exclude '.git'` é obrigatório — sem ele o `--delete` apaga o `.git` do destino
(aconteceu no primeiro teste).

**Senha:** em 20/10 ela **saiu dos arquivos versionados** (`HANDOFF.md` tinha o
literal — contra a regra do `AGENTS.md`). Agora só existe no
`.streamlit/secrets.toml` (PC) e nos *Secrets* da nuvem. O repositório é público:
**nada de senha, chave ou token em arquivo versionado.**

## 📱 Celular (20/10/2026)

A Raquel vai usar no celular — e celular precisa de outra medida. O que mudou
(tudo dentro de `@media (max-width: 640px)` no `CSS` do `app.py`):

| Antes | Agora |
|---|---|
| título em 2,25rem, quebrava em 2 linhas | 1,32rem, uma linha |
| barra do Streamlit **cobria** o título | `.block-container` com 3,4rem em cima |
| 5 pílulas em 3 linhas | **uma linha que rola** para o lado |
| "Hemograma compl…" (cortado) | o nome **quebra em 2 linhas** e aparece inteiro |
| botões de 2,1rem (pequenos pro dedo) | 2,5–2,6rem (~44 px) |
| "Deploy" no topo | escondido (é botão de quem programa) |
| campos com zoom involuntário no iPhone | fonte 16 px nos campos |

**Como foi conferido:** o navegador do OpenCode não deixa mudar o tamanho da
tela, então rodei um **Chrome headless** com `Emulation.setDeviceMetricsOverride`
(390 × 844, 2x) e tirei foto de tela. Scripts em `/tmp/opencode/` (`foto.py`,
`cdp.py`); o app rodou numa **cópia sem senha** (`_celular_teste.py`, apagada no
fim) para o print não precisar de login. Fotos antigas × novas comparadas.

## 🐞 Os dois bugs que apareceram no primeiro dia (e os consertos)
### 1. Core dump: `free(): corrupted unsorted chunks` (13:52)
**Sintoma:** o app estava no ar, eu cliquei em poucas pílulas seguidas e o
processo **abortou** (systemd levantou de novo em 5 s). No `journalctl`:
```
free(): corrupted unsorted chunks
Fatal Python error: Aborted
  ... http/client.py in _close_conn ← httplib2 ← googleapiclient
  ... src/planilha.py:92 in ler (folhas)
```
**Causa:** `_conectar()` tinha `@st.cache_resource` — ou seja, **um cliente do
Google (com seu `httplib2.Http`) compartilhado entre todas as rodadas**. A
própria httplib2 avisa: *"Not thread-safe, requires external synchronization"*.
O Streamlit roda cada rodada numa thread e, com dois cliques rápidos (ou duas
abas), duas rodadas usam o mesmo cliente ao mesmo tempo → **corrupção de
memória** (o abort vem depois, em qualquer `free`).
**Prova:** um teste com **um cliente para 8 threads** (só leituras) abortou com a
**mesma** mensagem em 2 de 3 rodadas; com **um cliente por thread**, 0 quedas.
**Conserto:** `@st.cache_resource` **fora** de `_conectar()` — clientes novos a
cada rodada. O que é caro (as **credenciais**, que exigem troca de token) ficou
em cache dentro de `src/acesso.credenciais()`, com trava. Custo medido: alguns
milissegundos por rodada.

### 2. Pílula desmarcada mandava o item para a **primeira folha**
`st.pills` é **toggle**: um segundo toque na folha atual **desmarca** (volta
`None`). O `_seletor` caía calado em `nomes[0]` — com "Compras do mercado" na
frente, um item digitado na tela de Consultas foi **parar em Compras** (visto
aqui, no teste de 20/10). **Conserto:** `folha_lembrada` guarda a última folha de
verdade; se a pílula voltar `None`, o app **volta para ela** (`st.rerun()`), em
vez de pular para a primeira. Provado na tela: item "Dentista" caiu na folha
certa e foi apagado depois.

## Pendências
- [x] **Publicado no Streamlit Cloud** (21/10/2026): https://raquel-anotacoes.streamlit.app
      Repositório **público** `hamiltonjau/raquel-anotacoes`, branch `main`,
      *main file* `app.py`, Python **3.12** nos *Secrets* configurados.
      **Como testei de fora:** entrei com a senha, a planilha e as 5 folhas
      carregaram (conta de serviço OK) e o envio de foto funcionou com o token
      dos *Secrets* (arquivo criado e apagado depois).
      **Reimplantar:** `bash sincronizar-publico.sh "mensagem"` — o Streamlit
      Cloud pega o push sozinho (~1 min). Mudança em `requirements.txt` pede
      *Reboot* no painel.
- [ ] **Token das fotos pode vencer** (a tela de consentimento do Google está em
      **"Testing"**): o *refresh token* pode expirar em ~7 dias. Se as fotos
      pararem de subir, rodar `autorizar-fotos.py` no PC de novo e colar o novo
      `[google_oauth]` nos *Secrets* do Streamlit Cloud (o app continua
      funcionando sem foto: mostra o erro em português e não perde o item).
- [ ] **Senha na internet**: a senha tem 6 dígitos e o app vai ficar público.
      Já entrou um **freio de tentativas** (espera de 2 s, 4 s, 8 s… até 60 s a
      partir do 3º erro, dentro da mesma sessão). Se quiser mais, é trocar por
      uma senha maior — é uma linha no `secrets.toml` + reiniciar o serviço.
- [ ] Mostrar para a Raquel como usa (ainda não viu o app). O `LEIA-ME.txt` já
      está escrito na língua dela.
