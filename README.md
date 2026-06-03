# Parrot Trips — In-Trip App

Aplicativo web da Parrot Trips para acompanhar uma viagem em grupo. Permite que viajantes se autentiquem via WhatsApp, acompanhem o roteiro, completem checklists pré-viagem e vejam o progresso da viagem em tempo real.

---

## URLs de Produção

| O quê | URL |
|---|---|
| **App (frontend)** | `https://parrot-trips-app-286.netlify.app` |
| **Backend (API)** | `https://parrot-trips-backend-428743191336.southamerica-east1.run.app` |
| **Planilha de conteúdo** | [Google Drive — Parrot Trips Conteúdo de Viagens](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP) |

---

## Arquitetura

```
WeTravel (externo)          Google Sheets               GCP
     │                           │                        │
     │  wetravel_trips       Planilha única          Cloud Run
     │  trip_travelers       (Viagens, Fases,        (backend)
     │                        Checklist, Links,           │
     ▼                         Roteiro)              Cloud Storage
  Supabase ◄── scripts Python ◄─┘                    (frontend)
(PostgreSQL)
```

### Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.13 + FastAPI + SQLAlchemy async |
| Banco | Supabase (PostgreSQL) |
| Auth | WhatsApp OTP + JWT |
| Deploy | GCP Cloud Run (backend) + Netlify (frontend) |
| Conteúdo | Google Sheets → scripts Python → Supabase |

---

## Estrutura do Repositório

```
/
├── Makefile                        # Comandos de deploy raiz
├── roadmap.md                      # Roadmap do projeto
├── backend/
│   ├── app/
│   │   ├── core/                   # Configurações (JWT, env vars)
│   │   ├── db/                     # Models SQLAlchemy + sessão
│   │   ├── middleware/             # JWT auth middleware
│   │   ├── routers/                # Endpoints HTTP
│   │   │   ├── admin.py            # /admin — operações de gestão
│   │   │   ├── auth.py             # /auth — OTP + JWT
│   │   │   ├── checklist.py        # /checklist — progresso
│   │   │   ├── profile.py          # /profile — perfil do viajante
│   │   │   ├── trip.py             # /me/trip — viagem e fases
│   │   │   └── users.py            # /users
│   │   └── services/               # Regras de negócio
│   │       ├── admin_service.py    # Import/reset via API
│   │       ├── checklist_service.py
│   │       ├── trip_service.py     # Fases + progresso date-driven
│   │       └── ...
│   ├── scripts/                    # Scripts de operação manual
│   │   ├── add_test_user.py        # Adicionar viajante de teste
│   │   ├── create_trip_sheets.py   # Criar planilha no Drive
│   │   ├── import_trip_content.py  # Planilha → Supabase
│   │   ├── reset_trip_content.py   # Apagar conteúdo do banco
│   │   └── reset_traveler_progress.py  # Zerar progresso
│   ├── Dockerfile                  # Imagem de produção
│   ├── .env                        # Variáveis locais (não commitado)
│   └── .env.production             # Variáveis de produção (não commitado)
├── frontend/
│   ├── src/
│   │   ├── app/                    # Router, providers (Auth, Trip)
│   │   ├── features/               # Telas por domínio
│   │   │   ├── auth/               # LoginScreen
│   │   │   ├── profile/            # ProfileScreen
│   │   │   └── trip/               # HomeScreen, PhaseDetails, DayDetails
│   │   └── shared/                 # ProgressBar, BottomNav, TopBar, API client
│   ├── netlify.toml                # Configuração Netlify (SPA redirect)
│   ├── .env.production             # VITE_API_URL (não commitado)
│   └── firebase.json               # (não utilizado — legado)
├── google-apps-script/
│   ├── Code.gs                     # Menu admin para Google Sheets
│   └── README.md                   # Instruções de instalação
└── PRODUCT_AND_SYSTEM_DESIGN/      # Documentação de produto
    ├── 11-guia-preenchimento-dados-viagem.md
    ├── 13-insercao-conteudo-viagem-google-sheets.md
    ├── 14-fluxo-planilhas-supabase-app.md
    ├── 15-deploy-gcp.md
    └── 16-guia-demo.md
```

---

## Como Rodar Localmente

### Pré-requisitos

- Python 3.13 + Poetry
- Node.js 18+
- Acesso ao Supabase (DATABASE_URL no `.env`)

### Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --port 8000 --reload
# ou: make dev (a partir da pasta backend/)
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

---

## Deploy

Todos os comandos rodam da **raiz do repositório**.

```bash
make deploy-backend    # Build Docker + push para Artifact Registry + deploy Cloud Run
make deploy-frontend   # Build React + deploy Netlify
make deploy            # Os dois juntos
make logs              # Logs do Cloud Run em tempo real
make backend-url       # Imprime a URL do backend
```

**Pré-requisitos para deploy do backend:**
- `gcloud` autenticado: `gcloud auth login angelo@parrottrips.com`
- `backend/.env.production` preenchido (copiar de `backend/.env.production.example`)
- `frontend/.env.production` com `VITE_API_URL=<url do cloud run>`

**Pré-requisitos para deploy do frontend:**
- `netlify-cli` instalado: `npm install -g netlify-cli`
- Autenticado: `netlify login`
- Site `parrot-trips-app` já criado no Netlify (feito uma vez)

Se o deploy falhar com 403 ou "Reauthentication required":
```bash
gcloud auth login angelo@parrottrips.com
gcloud auth configure-docker southamerica-east1-docker.pkg.dev --account=angelo@parrottrips.com
```

**GCP Project:** `jogo-da-vida-497700` | **Region:** `southamerica-east1` | **Account:** `angelo@parrottrips.com`

---

## Banco de Dados (Supabase)

### Tabelas principais

| Tabela | Função |
|---|---|
| `wetravel_trips` | Viagens importadas do WeTravel (uuid, title, start_date, end_date) |
| `users` | Viajantes e staff (phone, full_name, role) |
| `otp_codes` | Códigos OTP temporários para login |
| `trip_travelers` | Vínculo user ↔ viagem |
| `traveler_profiles` | Dados detalhados do viajante (passaporte, restrições, etc.) |
| `trip_phases` | Fases pré-trip e dias in-trip (phase_type, starts_at, sort_order) |
| `trip_phase_checklist_items` | Itens de checklist por fase |
| `trip_phase_links` | Links úteis por fase |
| `trip_activities` | Atividades por dia (tipo, horário, duração, preço) |
| `traveler_checklist_progress` | Progresso do checklist por viajante |
| `traveler_phase_progress` | Fases marcadas como completas por viajante |

### Origem dos dados

- **WeTravel:** `wetravel_trips` e `trip_travelers` — importados automaticamente
- **Google Sheets → scripts:** `trip_phases`, `trip_phase_checklist_items`, `trip_phase_links`, `trip_activities`
- **App (em tempo real):** `traveler_checklist_progress`, `traveler_phase_progress`

---

## Autenticação

Fluxo completo:

1. Usuário digita o número de WhatsApp no app
2. Backend gera OTP, salva em `otp_codes` e envia via WhatsApp Business API
3. Usuário digita o código recebido
4. Backend valida, cria/atualiza o `user` no Supabase, retorna JWT (validade: 14 dias)
5. Frontend salva o JWT no `localStorage` e o inclui em todas as requests via `Authorization: Bearer`

Rotas públicas (sem JWT): `/auth/*`, `/admin/*`, `/healthz`

---

## Conteúdo das Viagens — Fluxo Completo

### Planilha única no Google Drive

Uma planilha centralizada `"Parrot Trips — Conteúdo de Viagens"` com 5 abas:

| Aba | Conteúdo | Importada? |
|---|---|---|
| **Viagens** | Lista de trip_uuid, nome e datas (sincronizado via Sync Trips) | Não — só referência |
| **Fases** | Uma linha por fase pré-trip por viagem | Sim |
| **Checklist** | Um item por linha | Sim |
| **Links** | Um link por linha | Sim |
| **Roteiro** | Uma linha por atividade de cada dia | Sim |

Cada aba tem `trip_uuid` como primeira coluna.

### Menu Apps Script na planilha

Após instalar `google-apps-script/Code.gs` na planilha (`Extensions → Apps Script`), o menu **🦜 Parrot Trips** aparece com:

| Item | O que faz |
|---|---|
| 🔄 Sync Trips from Supabase | Atualiza a aba Viagens com viagens ativas do banco |
| Import Trip Content → Supabase | Lê Fases/Checklist/Links/Roteiro e importa para o banco |
| Reset Trip Content | Apaga fases, atividades e checklist do banco para uma viagem |
| Reset Traveler Progress | Zera a barra de progresso de todos os viajantes |

### Scripts Python (linha de comando)

```bash
cd backend

# Criar a planilha no Drive (primeira vez)
poetry run python scripts/create_trip_sheets.py --folder-id <ID> --use-adc

# Importar uma viagem (ou todas)
poetry run python scripts/import_trip_content.py --trip-uuid TEST-2026-FULL
poetry run python scripts/import_trip_content.py --all

# Zerar progresso dos viajantes (~1 semana antes da partida)
poetry run python scripts/reset_traveler_progress.py --trip-uuid TEST-2026-FULL

# Apagar conteúdo do banco para uma viagem
poetry run python scripts/reset_trip_content.py --trip-uuid TEST-2026-FULL
```

---

## Barra de Progresso

### Modo pré-trip (antes da data de início)

- Conta fases pré-trip completadas pelo viajante
- Começa em 0%, avança ao marcar fases, **regressa ao desmarcar**
- O passarinho (ideal pace) acompanha o viajante

### Modo in-trip (a partir da data de início)

- Calculado automaticamente: `fases cujo starts_at <= agora`
- Avança sozinho conforme os dias passam — sem ação manual
- Passarinho e viajante andam juntos (ambos date-driven)

### Transição

A equipe roda `reset_traveler_progress.py` ~1 semana antes da partida. O app detecta automaticamente qual modo exibir baseado na `start_date` da viagem.

---

## API Admin (sem autenticação)

Endpoints para uso interno via Apps Script ou curl:

```bash
BACKEND=https://parrot-trips-backend-428743191336.southamerica-east1.run.app

# Listar viagens ativas
GET $BACKEND/admin/trips

# Importar conteúdo de uma viagem da planilha
POST $BACKEND/admin/trips/import        {"trip_uuid": "..."}

# Apagar conteúdo do banco para uma viagem
POST $BACKEND/admin/trips/reset-content {"trip_uuid": "..."}

# Zerar progresso dos viajantes
POST $BACKEND/admin/trips/reset-progress {"trip_uuid": "..."}
```

---

## Endpoints da API (autenticados via JWT)

| Método | Endpoint | Uso |
|---|---|---|
| `POST` | `/auth/request-otp` | Solicitar OTP via WhatsApp |
| `POST` | `/auth/verify-otp` | Validar OTP e receber JWT |
| `GET` | `/me/trip` | Dados da viagem do usuário |
| `GET` | `/me/trip/phases` | Fases + checklist + links |
| `GET` | `/me/trip/phases/{id}` | Fase específica com atividades |
| `GET` | `/me/trip/travelers` | Viajantes com posição atual |
| `GET` | `/profile/{user_id}` | Perfil completo |
| `PUT` | `/profile/{user_id}` | Atualizar perfil |
| `POST` | `/checklist/update` | Marcar/desmarcar item de checklist |
| `GET` | `/checklist/{trip_id}/{user_id}` | Progresso do checklist |
| `POST` | `/phases/complete` | Marcar/desmarcar fase como completa |
| `GET` | `/phases/{trip_id}/{user_id}` | Fases completadas |

---

## Viagem de Teste

Para desenvolvimento e demos:

| Campo | Valor |
|---|---|
| `trip_uuid` | `TEST-2026-FULL` |
| Nome | Viagem de Teste — Full Coverage |
| Data início | 2026-07-01 |

### Cadastrar um viajante de teste

```bash
cd backend
poetry run python scripts/add_test_user.py \
  --phone +5511999999999 \
  --name "Nome" \
  --trip-uuid TEST-2026-FULL

# Remover depois da demo:
poetry run python scripts/add_test_user.py --phone +5511999999999 --remove
```

**Viajantes atuais na viagem de teste:**
- Marcelo Angelo (+5512991296651)
- Vitor Sanches (+5511997666680)
- Becker (+5511981121225)
- Bia (+5511997220065)
- Bela (+5534992526835)
- Karen (+5511973653160)
- Jaqueline (+5512991479500)

---

## Variáveis de Ambiente

### `backend/.env` (local) e `backend/.env.production` (produção)

```
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_TEMPLATE_NAME=intripauth
WHATSAPP_TEMPLATE_LANGUAGE=en
SUPABASE_ANON_KEY=...
TRIP_CONTENT_SHEET_ID=1N1B66s1-K4DDf2_863frmhnpF6LRZB_ww60uax0gKZM
GCP_SERVICE_ACCOUNT_JSON=secrets/gcp-service-account.json
```

### `frontend/.env.production`

```
VITE_API_URL=https://parrot-trips-backend-428743191336.southamerica-east1.run.app
```

---

## Documentação Adicional

Toda a documentação de produto e sistema está em `PRODUCT_AND_SYSTEM_DESIGN/`:

| Arquivo | Conteúdo |
|---|---|
| `11-guia-preenchimento-dados-viagem.md` | Como preencher a planilha de conteúdo |
| `13-insercao-conteudo-viagem-google-sheets.md` | Estrutura da planilha e scripts |
| `14-fluxo-planilhas-supabase-app.md` | Fluxo completo planilha → Supabase → app com diagramas |
| `15-deploy-gcp.md` | Guia operacional de deploy na GCP |
| `16-guia-demo.md` | Como preparar e conduzir uma demo |
