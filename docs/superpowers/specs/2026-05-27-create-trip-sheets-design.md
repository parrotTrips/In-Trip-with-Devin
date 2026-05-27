# Design: Script de Criação de Planilhas de Viagem no Google Sheets

**Data:** 2026-05-27
**Status:** Aprovado

---

## Contexto

O app Parrot Trips exibe conteúdo de viagem (fases pré-trip, roteiro dia a dia, atividades) a partir do banco Supabase. Para popular esse conteúdo, o time Parrot Trips preenche planilhas Google Sheets que depois são importadas para o banco via script.

Este spec cobre a **primeira etapa do pipeline**: criar automaticamente as planilhas estruturadas no Google Drive, prontas para preenchimento pelo time.

---

## Objetivo

Criar o script `backend/scripts/create_trip_sheets.py` que:

1. Lê todas as viagens registradas em `wetravel_trips` no Supabase
2. Para cada viagem, cria um arquivo Google Sheets em uma pasta do Google Drive
3. Estrutura as abas `Config`, `Pre-Trip` e `Roteiro` com cabeçalhos e linhas de exemplo
4. Preenche a aba `Config` automaticamente com os metadados da viagem vindos do banco

---

## Fora de escopo

- Importação dos dados preenchidos de volta para o banco (próximo script: `import_trip_content.py`)
- Atualização de planilhas já existentes
- Validação do conteúdo preenchido pelo time

---

## Script: `create_trip_sheets.py`

### Localização

`backend/scripts/create_trip_sheets.py`

### Execução

```bash
cd backend
poetry run python scripts/create_trip_sheets.py \
  --folder-id <ID_DA_PASTA_NO_GOOGLE_DRIVE>
```

O folder ID está na URL da pasta: `https://drive.google.com/drive/folders/<FOLDER_ID>`

### Comportamento

1. Conecta ao banco Supabase via `DATABASE_URL` do `.env`
2. Lê `SELECT trip_uuid, title, start_date, end_date FROM wetravel_trips ORDER BY start_date`
3. Autentica na Google Sheets/Drive API com a service account em `GCP_SERVICE_ACCOUNT_JSON`
4. Para cada viagem:
   - Verifica se já existe arquivo com o mesmo nome na pasta (idempotência por nome)
   - Se já existe: pula, registra no log como "skipped"
   - Se não existe: cria o arquivo, estrutura as abas, registra como "created"
5. Imprime resumo final: criadas / puladas, e URL de cada planilha

### Nome do arquivo gerado

```
[YYYY-MM-DD] [trip_uuid] — [trip_title]
```

Exemplo: `2026-12-26 gsb-nye-brazil-2026 — GSB NYE Brazil Trek`

---

## Estrutura das abas

### Aba `Config`

Cabeçalho: `chave` | `valor`

Linhas geradas automaticamente pelo script:

| chave | valor |
|---|---|
| trip_uuid | (vem do banco) |
| trip_title | (vem do banco) |
| start_date | YYYY-MM-DD (vem do banco) |
| end_date | YYYY-MM-DD (vem do banco) |

### Aba `Pre-Trip`

Colunas: `fase` | `bloco` | `ordem` | `campo` | `valor`

O script insere o cabeçalho e linhas de exemplo para as 4 fases fixas (visa, vaccination, packing, documents):

- 1 linha de `header` com campos `title`, `subtitle`, `icon`, `short_description`, `detailed_description`
- 2 linhas de `checklist` com campos `label`, `is_required`
- 1 linha de `link` com campos `label`, `url`

Valores de exemplo são genéricos (ex: "Verificar requisitos de visto") para orientar o preenchimento sem conteúdo específico.

### Aba `Roteiro`

Colunas (14): `dia` | `data` | `dia_titulo` | `dia_subtitulo` | `dia_icon` | `dia_descricao_curta` | `dia_descricao_completa` | `atividade_nome` | `atividade_tipo` | `atividade_horario` | `atividade_duracao_min` | `atividade_descricao_curta` | `atividade_info_pratica` | `atividade_preco_brl`

O script insere o cabeçalho e 1 linha de exemplo (Day 1 / Transfer logístico).

### Formatação

- Cabeçalhos em negrito
- Primeira linha congelada (freeze row 1) em todas as abas
- Largura das colunas ajustada automaticamente (autoResize)

---

## Setup e dependências

### Dependências Python

```toml
# pyproject.toml
google-auth = ">=2.0"
google-auth-httplib2 = ">=0.1"
google-api-python-client = ">=2.0"
asyncpg = ">=0.27"     # já presente
```

### Variáveis de ambiente (`backend/.env`)

```
GCP_SERVICE_ACCOUNT_JSON=secrets/gcp-service-account.json
```

### Service account GCP

1. GCP Console → IAM & Admin → Service Accounts → Create
2. Nome: `parrot-trips-sheets-creator`
3. Habilitar APIs: Google Sheets API + Google Drive API
4. Baixar chave JSON → salvar em `backend/secrets/gcp-service-account.json` (gitignored)
5. Compartilhar a pasta do Google Drive com o e-mail da service account (Editor)

### `.gitignore`

Verificar que `backend/secrets/` está no `.gitignore`. Adicionar se necessário.

---

## Saída esperada

```
Conectando ao banco... OK
Viagens encontradas: 7

[1] GSB NYE Brazil Trek
    ✅ Criada: https://docs.google.com/spreadsheets/d/...

[2] Wharton Brazil Trek December 2026
    ⏭ Pulada: já existe na pasta

[3] UCLA Carnival 27 Trek
    ✅ Criada: https://docs.google.com/spreadsheets/d/...

...

Concluído: 6 criadas, 1 pulada
```

---

## Próximo passo

Após o time preencher as planilhas: implementar `backend/scripts/import_trip_content.py` para ler cada planilha e fazer upsert no banco Supabase (trip_phases, trip_phase_checklist_items, trip_phase_links, trip_activities).
