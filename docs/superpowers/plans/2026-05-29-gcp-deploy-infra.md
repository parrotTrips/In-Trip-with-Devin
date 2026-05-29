# GCP Deploy Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar Dockerfile, .dockerignore, configuração Firebase Hosting e Makefile raiz para fazer deploy do backend no Cloud Run e do frontend no Firebase Hosting no projeto GCP `jogo-da-vida-497700`.

**Architecture:** Backend FastAPI empacotado em Docker, publicado no Artifact Registry e servido pelo Cloud Run (escala a zero, cobra por request). Frontend React buildado com Vite e servido pelo Firebase Hosting (CDN estático, gratuito). Variáveis de ambiente configuradas diretamente no Cloud Run via `--set-env-vars`. Makefile raiz orquestra tudo com comandos simples.

**Tech Stack:** Docker, Google Cloud Run, Google Artifact Registry, Firebase Hosting, gcloud CLI, Firebase CLI, GNU Make, Python 3.13 (Poetry), React + Vite

---

## Contexto do projeto

- **GCP Project ID:** `jogo-da-vida-497700`
- **GCP Region:** `southamerica-east1` (São Paulo — mais próximo dos usuários brasileiros)
- **Cloud Run service name:** `parrot-trips-backend`
- **Artifact Registry repo:** `parrot-trips` (a criar)
- **Firebase Hosting site:** `parrot-trips` (a criar)
- **Backend:** `backend/` — FastAPI com Poetry, Python 3.13
- **Frontend:** `frontend/` — React + Vite, `npm run build` gera `dist/`
- **Conta GCP ativa:** `angelo@parrottrips.com`

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/Dockerfile` | Criar | Imagem de produção do backend FastAPI |
| `backend/.dockerignore` | Criar | Exclui secrets, cache, env local do contexto Docker |
| `frontend/firebase.json` | Criar | Config do Firebase Hosting (aponta para `dist/`) |
| `frontend/.firebaserc` | Criar | Associa o projeto ao Firebase project ID |
| `Makefile` | Criar | Comandos de deploy raiz: `deploy`, `deploy-backend`, `deploy-frontend`, `logs`, `open` |

---

## Task 1: Habilitar APIs GCP necessárias

**Files:** nenhum arquivo — apenas comandos gcloud

- [ ] **Step 1: Habilitar as APIs necessárias**

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --account=angelo@parrottrips.com \
  --project=jogo-da-vida-497700
```

Expected output (pode demorar 1-2 min):
```
Operation "operations/acf..." finished successfully.
```

- [ ] **Step 2: Criar repositório no Artifact Registry**

```bash
gcloud artifacts repositories create parrot-trips \
  --repository-format=docker \
  --location=southamerica-east1 \
  --description="Parrot Trips Docker images" \
  --account=angelo@parrottrips.com \
  --project=jogo-da-vida-497700
```

Expected:
```
Created repository [parrot-trips].
```

- [ ] **Step 3: Configurar Docker para autenticar no Artifact Registry**

```bash
gcloud auth configure-docker southamerica-east1-docker.pkg.dev \
  --account=angelo@parrottrips.com \
  --project=jogo-da-vida-497700
```

Expected:
```
Adding credentials for: southamerica-east1-docker.pkg.dev
```

- [ ] **Step 4: Confirmar que tudo está habilitado**

```bash
gcloud services list --enabled \
  --account=angelo@parrottrips.com \
  --project=jogo-da-vida-497700 \
  --filter="name:(run.googleapis.com OR artifactregistry.googleapis.com OR cloudbuild.googleapis.com)"
```

Expected: as 3 APIs listadas com status ENABLED.

- [ ] **Step 5: Commit (arquivo de documentação)**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add .
git commit -m "chore: nota — APIs GCP habilitadas para deploy (Cloud Run, Artifact Registry, Cloud Build)"
```

---

## Task 2: Dockerfile do backend

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

- [ ] **Step 1: Criar `backend/.dockerignore`**

Criar o arquivo `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/.dockerignore` com este conteúdo:

```
# Ambiente virtual local
env/
.venv/
__pycache__/
*.pyc
*.pyo

# Secrets e configuração local
.env
secrets/

# Artefatos de teste e build
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/

# Banco de dados local
*.db
*.sqlite

# Arquivos de IDE
.idea/
.vscode/
*.swp
```

- [ ] **Step 2: Criar `backend/Dockerfile`**

Criar o arquivo `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/Dockerfile` com este conteúdo:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Instala Poetry
RUN pip install poetry==1.8.5

# Copia arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Instala dependências de produção (sem dev, sem criar virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copia código da aplicação
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Porta padrão do Cloud Run
ENV PORT=8080

# Inicia o servidor
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
```

- [ ] **Step 3: Fazer build local para testar**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend
docker build -t parrot-trips-backend:local .
```

Expected: build finaliza sem erros, última linha similar a:
```
Successfully built <hash>
Successfully tagged parrot-trips-backend:local
```

- [ ] **Step 4: Testar que o container sobe (sem banco — só verifica o boot)**

```bash
docker run --rm -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://x:x@localhost/x" \
  -e JWT_SECRET="test" \
  -e WHATSAPP_PHONE_NUMBER_ID="" \
  -e WHATSAPP_ACCESS_TOKEN="" \
  -e WHATSAPP_TEMPLATE_NAME="intripauth" \
  parrot-trips-backend:local &

sleep 3 && curl -s http://localhost:8080/health | head -c 200
kill %1 2>/dev/null || true
```

Expected: resposta JSON do endpoint `/health` (pode ser erro de DB — o que importa é o app subir).

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add backend/Dockerfile backend/.dockerignore
git commit -m "feat: add Dockerfile and .dockerignore for Cloud Run deploy"
```

---

## Task 3: Configuração Firebase Hosting

**Files:**
- Create: `frontend/firebase.json`
- Create: `frontend/.firebaserc`

**Pré-requisito:** Firebase CLI instalado. Verificar com `firebase --version`. Se não estiver:
```bash
npm install -g firebase-tools
```
E autenticar:
```bash
firebase login
```

- [ ] **Step 1: Criar `frontend/firebase.json`**

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/firebase.json`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "/assets/**",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      },
      {
        "source": "**",
        "headers": [
          {
            "key": "X-Frame-Options",
            "value": "SAMEORIGIN"
          }
        ]
      }
    ]
  }
}
```

O `"rewrites"` garante que o React Router funciona — todas as rotas caem no `index.html`.

- [ ] **Step 2: Criar `frontend/.firebaserc`**

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/.firebaserc`:

```json
{
  "projects": {
    "default": "jogo-da-vida-497700"
  }
}
```

- [ ] **Step 3: Fazer build do frontend**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
npm run build 2>&1 | tail -5
```

Expected:
```
✓ built in Xms
```

- [ ] **Step 4: Verificar que o Firebase CLI reconhece a configuração**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend
firebase hosting:channel:list --project=jogo-da-vida-497700 2>&1 | head -10
```

Se Firebase Hosting ainda não está inicializado no projeto, o comando vai dar erro controlado — isso é esperado e o Makefile vai lidar com isso no deploy.

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add frontend/firebase.json frontend/.firebaserc
git commit -m "feat: add Firebase Hosting config for frontend deploy"
```

---

## Task 4: Makefile raiz

**Files:**
- Create: `Makefile` (na raiz do repositório)

O Makefile raiz é o ponto central de operação. Todos os comandos assumem que `gcloud` está autenticado com `angelo@parrottrips.com` e o projeto `jogo-da-vida-497700`.

- [ ] **Step 1: Criar `Makefile` na raiz**

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/Makefile`:

```makefile
# ── Configuração ──────────────────────────────────────────────────────────────
GCP_PROJECT    = jogo-da-vida-497700
GCP_ACCOUNT    = angelo@parrottrips.com
GCP_REGION     = southamerica-east1
SERVICE_NAME   = parrot-trips-backend
IMAGE_REPO     = $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/parrot-trips/backend
FIREBASE_PROJECT = $(GCP_PROJECT)

# Tag da imagem: usa o hash curto do commit atual
IMAGE_TAG      ?= $(shell git rev-parse --short HEAD)
IMAGE          = $(IMAGE_REPO):$(IMAGE_TAG)

# ── Deploy completo ────────────────────────────────────────────────────────────
.PHONY: deploy
deploy: deploy-backend deploy-frontend
	@echo ""
	@echo "Deploy completo."
	@$(MAKE) open

# ── Backend ───────────────────────────────────────────────────────────────────
.PHONY: deploy-backend
deploy-backend: docker-build docker-push cloud-run-deploy

.PHONY: docker-build
docker-build:
	@echo "Building Docker image $(IMAGE)..."
	docker build -t $(IMAGE) backend/

.PHONY: docker-push
docker-push:
	@echo "Pushing image to Artifact Registry..."
	docker push $(IMAGE)

.PHONY: cloud-run-deploy
cloud-run-deploy:
	@echo "Deploying to Cloud Run..."
	@if [ ! -f backend/.env.production ]; then \
		echo "ERROR: backend/.env.production not found."; \
		echo "Copy backend/.env.production.example and fill in the values."; \
		exit 1; \
	fi
	gcloud run deploy $(SERVICE_NAME) \
		--image=$(IMAGE) \
		--region=$(GCP_REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--env-vars-file=backend/.env.production \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT)
	@echo "Backend URL:"
	@gcloud run services describe $(SERVICE_NAME) \
		--region=$(GCP_REGION) \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT) \
		--format="value(status.url)"

# ── Frontend ──────────────────────────────────────────────────────────────────
.PHONY: deploy-frontend
deploy-frontend: frontend-build firebase-deploy

.PHONY: frontend-build
frontend-build:
	@echo "Building frontend..."
	cd frontend && npm run build

.PHONY: firebase-deploy
firebase-deploy:
	@echo "Deploying to Firebase Hosting..."
	cd frontend && firebase deploy --only hosting --project=$(FIREBASE_PROJECT)

# ── Operação ──────────────────────────────────────────────────────────────────
.PHONY: logs
logs:
	gcloud run services logs tail $(SERVICE_NAME) \
		--region=$(GCP_REGION) \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT)

.PHONY: backend-url
backend-url:
	@gcloud run services describe $(SERVICE_NAME) \
		--region=$(GCP_REGION) \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT) \
		--format="value(status.url)"

.PHONY: open
open:
	@BACKEND=$$(gcloud run services describe $(SERVICE_NAME) \
		--region=$(GCP_REGION) \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT) \
		--format="value(status.url)" 2>/dev/null); \
	FRONTEND="https://$(GCP_PROJECT).web.app"; \
	echo "Backend:  $$BACKEND"; \
	echo "Frontend: $$FRONTEND"; \
	open $$BACKEND/health 2>/dev/null || xdg-open $$BACKEND/health 2>/dev/null || true; \
	open $$FRONTEND 2>/dev/null || xdg-open $$FRONTEND 2>/dev/null || true

# ── Desenvolvimento local ──────────────────────────────────────────────────────
.PHONY: dev-backend
dev-backend:
	cd backend && make dev

.PHONY: dev-frontend
dev-frontend:
	cd frontend && npm run dev

.PHONY: test
test:
	cd backend && make test

.PHONY: help
help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "  Deploy:"
	@echo "    make deploy              — backend + frontend juntos"
	@echo "    make deploy-backend      — só o backend (Cloud Run)"
	@echo "    make deploy-frontend     — só o frontend (Firebase Hosting)"
	@echo ""
	@echo "  Operação:"
	@echo "    make logs                — tail dos logs do Cloud Run"
	@echo "    make backend-url         — imprime a URL do backend"
	@echo "    make open                — abre backend e frontend no browser"
	@echo ""
	@echo "  Desenvolvimento:"
	@echo "    make dev-backend         — sobe o backend local"
	@echo "    make dev-frontend        — sobe o frontend local"
	@echo "    make test                — roda os testes do backend"
	@echo ""
	@echo "  Variáveis:"
	@echo "    IMAGE_TAG=<tag>          — sobrescreve a tag da imagem (padrão: git commit hash)"
	@echo "    Ex: make deploy-backend IMAGE_TAG=v1.2.3"
```

- [ ] **Step 2: Criar `backend/.env.production.example`**

Criar `/Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/.env.production.example`:

```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
JWT_SECRET=coloque-um-secret-longo-e-aleatorio-aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=seu_waba_id
WHATSAPP_ACCESS_TOKEN=seu_access_token
WHATSAPP_TEMPLATE_NAME=intripauth
WHATSAPP_TEMPLATE_LANGUAGE=en
SUPABASE_ANON_KEY=sua_anon_key
TRIP_CONTENT_SHEET_ID=id_da_planilha_no_sheets
```

O formato `--env-vars-file` do `gcloud run deploy` aceita um arquivo no formato `KEY=VALUE` (um por linha, sem aspas). Este arquivo é o template — o arquivo real `backend/.env.production` é gitignored.

- [ ] **Step 3: Adicionar `.env.production` ao .gitignore**

Verificar se já existe `.gitignore` na raiz:

```bash
cat /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/.gitignore 2>/dev/null || echo "nao existe"
```

Se não existir, criar. Se existir, adicionar a linha. O arquivo deve conter pelo menos:

```
backend/.env.production
backend/secrets/
```

- [ ] **Step 4: Verificar que o Makefile é válido**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make help
```

Expected: imprime a lista de comandos sem erros de sintaxe.

- [ ] **Step 5: Commit**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
git add Makefile backend/.env.production.example
git commit -m "feat: add root Makefile and .env.production.example for GCP deploy"
```

---

## Task 5: Primeiro deploy completo

**Files:** nenhum arquivo novo — apenas execução

**Pré-requisito:** Criar `backend/.env.production` copiando o `.example` e preenchendo com os valores reais de `backend/.env`.

- [ ] **Step 1: Criar backend/.env.production a partir do .env real**

```bash
cp /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/.env \
   /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/.env.production
```

Verificar que o arquivo não tem linhas com `#` (comentários) ou valores vazios que quebrem o `--env-vars-file`. Remover comentários se necessário:

```bash
grep -v "^#" /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/backend/.env.production | grep -v "^$"
```

- [ ] **Step 2: Deploy do backend**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make deploy-backend
```

Expected ao final:
```
Backend URL:
https://parrot-trips-backend-XXXXXXXX-rj.a.run.app
```

- [ ] **Step 3: Testar o backend deployado**

```bash
BACKEND_URL=$(make backend-url)
curl -s "$BACKEND_URL/health"
```

Expected: resposta JSON do health check.

- [ ] **Step 4: Configurar VITE_API_URL no frontend e fazer deploy**

Antes do deploy do frontend, criar `frontend/.env.production` com a URL do backend:

```bash
BACKEND_URL=$(cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin && make backend-url)
echo "VITE_API_URL=$BACKEND_URL" > /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin/frontend/.env.production
```

Depois:

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
make deploy-frontend
```

Expected ao final:
```
Hosting URL: https://jogo-da-vida-497700.web.app
```

- [ ] **Step 5: Testar o frontend deployado**

```bash
make open
```

Verificar no browser:
- Frontend carrega em `https://jogo-da-vida-497700.web.app`
- Tela de login aparece
- Health do backend responde em `https://parrot-trips-backend-XXXXXXXX-rj.a.run.app/health`

- [ ] **Step 6: Adicionar .env.production do frontend ao .gitignore e commit final**

```bash
cd /Users/masfz/Programacao/parrot_trips/In-Trip-with-Devin
echo "frontend/.env.production" >> .gitignore
git add .gitignore
git commit -m "chore: ignore frontend/.env.production"
```

---

## Self-review

**Spec coverage:**
- ✅ Dockerfile backend
- ✅ .dockerignore backend
- ✅ firebase.json + .firebaserc frontend
- ✅ Makefile raiz com deploy, deploy-backend, deploy-frontend, logs, open
- ✅ .env.production.example
- ✅ APIs GCP habilitadas
- ✅ Artifact Registry criado
- ✅ Primeiro deploy end-to-end

**Placeholder scan:** Nenhum TBD ou TODO encontrado.

**Consistência:**
- `IMAGE_REPO` e `IMAGE` no Makefile são consistentes entre `docker-build`, `docker-push` e `cloud-run-deploy`.
- `GCP_PROJECT`, `GCP_REGION`, `GCP_ACCOUNT` definidos uma vez e reusados em todos os targets.
- `backend/.env.production` referenciado tanto no Makefile (`--env-vars-file`) quanto no .gitignore.
