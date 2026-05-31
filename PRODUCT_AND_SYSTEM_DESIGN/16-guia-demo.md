# Guia de Demo — Parrot Trips

Como preparar e conduzir uma demonstração do aplicativo para colegas ou stakeholders, mostrando tanto o lado técnico (planilha → Supabase) quanto o lado do viajante (autenticação e navegação no app).

---

## O que a demo mostra

**Lado técnico (você conduz):**
- Como o conteúdo de uma viagem é estruturado em uma planilha Google Sheets
- Como um script importa esse conteúdo para o banco de dados (Supabase)
- O dado aparecendo em tempo real no aplicativo após o import

**Lado do viajante (seu convidado experimenta):**
- Acesso ao app pelo browser (sem instalação)
- Autenticação via WhatsApp OTP
- Navegação pelas fases pré-viagem, checklist e roteiro
- Barra de progresso interativa

---

## Preparação antes da demo

### 1. Preencher a planilha com conteúdo apresentável

A planilha da Viagem de Teste tem hoje apenas dados de exemplo genéricos. Antes da demo, vale substituir pelo menos algumas linhas com conteúdo real e legível.

Abrir a planilha: [Parrot Trips — Conteúdo de Viagens](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP)

Filtrar pelas linhas com `trip_uuid = TEST-2026-FULL` e editar as abas:
- **Fases** — títulos e descrições das fases pré-viagem
- **Checklist** — itens de checklist de cada fase
- **Roteiro** — dias e atividades da viagem

### 2. Cadastrar o convidado

```bash
cd backend
poetry run python scripts/add_test_user.py \
  --phone +5511999999999 \
  --name "Nome do Convidado" \
  --trip-uuid TEST-2026-FULL
```

O número deve ser o WhatsApp real da pessoa — ela receberá o código OTP nesse número.

### 3. Verificar que o app está no ar

```bash
# Backend respondendo?
curl -s -o /dev/null -w "%{http_code}\n" \
  https://parrot-trips-backend-428743191336.southamerica-east1.run.app/health
# Esperado: 401 (app no ar, auth middleware interceptando — normal)

# Frontend carregando?
curl -s -o /dev/null -w "%{http_code}\n" \
  https://storage.googleapis.com/parrot-trips-frontend/index.html?v=0ac2ee8
# Esperado: 200
```

Se o backend não responder, fazer deploy:
```bash
make deploy-backend
```

---

## Roteiro da demo

### Parte 1 — O lado técnico (5–10 min)

**1. Mostrar o banco vazio**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
poetry run python scripts/reset_trip_content.py --trip-uuid TEST-2026-FULL --dry-run
```

Isso mostra quantas fases, itens e atividades existem atualmente. Se tiver dados antigos, limpar:

```bash
poetry run python scripts/reset_trip_content.py --trip-uuid TEST-2026-FULL
```

**2. Mostrar a planilha**

Abrir a [planilha no Google Sheets](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP) e percorrer as abas:
- **Viagens** — lista de viagens com UUID e datas
- **Fases** — uma linha por fase pré-viagem, `trip_uuid` na primeira coluna
- **Checklist** — itens de cada fase
- **Roteiro** — dias e atividades

Mostrar que a primeira coluna em todas as abas é o `trip_uuid` — isso é o que vincula o conteúdo à viagem certa.

**3. Rodar o import**

```bash
poetry run python scripts/import_trip_content.py --trip-uuid TEST-2026-FULL
```

> Todos os comandos `poetry run` precisam ser executados de dentro da pasta `backend/`.

Output esperado:
```
Connecting to Google Sheets...
Reading Fases tab...
  4 fase(s): ['visa', 'vaccination', 'packing', 'documents']
Reading Checklist tab...
Reading Links tab...
Reading Roteiro tab...
  1 day(s), 1 activit(ies)

Connecting to database...

Import complete!
   Pre-trip phases : 4
   Checklist items : 8
   Links           : 4
   In-trip days    : 1
   Activities      : 1
```

**4. Abrir o app e mostrar o conteúdo aparecendo**

```bash
open https://storage.googleapis.com/parrot-trips-frontend/index.html?v=0ac2ee8
```

---

### Parte 2 — O lado do viajante (5–10 min)

**1. O convidado acessa o link**

```
https://storage.googleapis.com/parrot-trips-frontend/index.html?v=0ac2ee8
```

Pode compartilhar pelo WhatsApp, email ou mostrar o QR code da URL.

**2. Autenticação via WhatsApp**

- Digitar o número de telefone (com DDI, ex: `+5511999999999`)
- Receber o código OTP no WhatsApp
- Digitar o código no app
- Entrar direto na viagem

**3. Navegar pelo app**

Pontos a destacar durante a navegação:

- **HomeScreen** — barra de progresso, game board com todas as fases
- **Fase pré-viagem** — título, descrição, checklist interativo, links úteis
- **Marcar um item do checklist** — barra avança em tempo real
- **Roteiro** — dias da viagem, atividades com tipo (inclusa, opcional, logística)
- **Viajantes** — avatares dos outros participantes e onde cada um está no caminho

---

## Comandos de referência rápida

> Todos os comandos `poetry run` precisam ser executados de dentro da pasta `backend/`:
> ```bash
> cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
> ```

```bash
# Limpar conteúdo da viagem de teste (sem apagar a viagem)
poetry run python scripts/reset_trip_content.py --trip-uuid TEST-2026-FULL

# Importar conteúdo da planilha
poetry run python scripts/import_trip_content.py --trip-uuid TEST-2026-FULL

# Cadastrar um convidado
poetry run python scripts/add_test_user.py \
  --phone +5511999999999 \
  --name "Nome" \
  --trip-uuid TEST-2026-FULL

# Remover um convidado após a demo
poetry run python scripts/add_test_user.py \
  --phone +5511999999999 \
  --remove

# Ver logs do backend em tempo real (para mostrar requests chegando)
# Rodar da raiz do repositório:
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make logs
```

---

## URLs

| O quê | URL |
|---|---|
| App (frontend) | `https://storage.googleapis.com/parrot-trips-frontend/index.html?v=0ac2ee8` |
| Backend (API) | `https://parrot-trips-backend-428743191336.southamerica-east1.run.app` |
| Planilha de conteúdo | [Google Drive — pasta de viagens](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP) |
| Supabase | Dashboard do projeto no Supabase |

---

## Viagem de teste

| Campo | Valor |
|---|---|
| `trip_uuid` | `TEST-2026-FULL` |
| Nome | Viagem de Teste — Full Coverage |
| Data início | 2026-07-01 |

A viagem de teste existe exclusivamente para demos e desenvolvimento — pode limpar e reimportar quantas vezes quiser sem afetar as viagens reais.
