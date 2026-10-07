# ── Configuração ──────────────────────────────────────────────────────────────
GCP_PROJECT    = jogo-da-vida-497700
GCP_ACCOUNT    = angelo@parrottrips.com
GCP_REGION     = southamerica-east1
SERVICE_NAME   = parrot-trips-backend
IMAGE_REPO     = $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/parrot-trips/backend
NETLIFY_SITE     = e5840ec7-de34-4fbb-a115-ccf7e3292999
NETLIFY_SITE_NAME = parrot-trips
FRONTEND_URL     = https://$(NETLIFY_SITE_NAME).netlify.app

# Image tag: uses short git commit hash by default
IMAGE_TAG      ?= $(shell git rev-parse --short HEAD)
IMAGE          = $(IMAGE_REPO):$(IMAGE_TAG)

# Homologação always uses resources and secret files distinct from production.
HOMOLOG_SERVICE_NAME      = parrot-trips-backend-homolog
HOMOLOG_IMAGE             = $(IMAGE_REPO):$(IMAGE_TAG)-homolog
HOMOLOG_NETLIFY_SITE      ?= bce4a7d3-2186-4bdf-b39e-ae21ea821b0e
HOMOLOG_NETLIFY_SITE_NAME ?= parrot-trips-homolog
HOMOLOG_FRONTEND_URL      = https://$(HOMOLOG_NETLIFY_SITE_NAME).netlify.app
HOMOLOG_BACKEND_ENV_FILE  = backend/.env.homologation
HOMOLOG_FRONTEND_ENV_FILE = frontend/.env.homologation
HOMOLOG_DATABASE_SECRET   = parrot-trips-homolog-database-url
HOMOLOG_JWT_SECRET        = parrot-trips-homolog-jwt-secret
SYNC_PYTHON              ?= backend/.venv/bin/python
HOMOLOG_SUPABASE_REF      = lgpniurbguguragmubui
HOMOLOG_DB_KEYCHAIN       = parrot-trips-homolog-supabase-db

# ── Guardas de homologação ───────────────────────────────────────────────────
.PHONY: check-homolog-config
check-homolog-config:
	@test -n "$(HOMOLOG_SERVICE_NAME)" || { echo "ERROR: HOMOLOG_SERVICE_NAME is required."; exit 1; }
	@test "$(HOMOLOG_SERVICE_NAME)" != "$(SERVICE_NAME)" || { echo "ERROR: homologation must use a different Cloud Run service."; exit 1; }
	@test -n "$(HOMOLOG_NETLIFY_SITE)" || { echo "ERROR: HOMOLOG_NETLIFY_SITE is required."; exit 1; }
	@test "$(HOMOLOG_NETLIFY_SITE)" != "$(NETLIFY_SITE)" || { echo "ERROR: homologation must use a different Netlify site."; exit 1; }
	@test "$(HOMOLOG_BACKEND_ENV_FILE)" != "backend/.env.production" || { echo "ERROR: homologation must not use the production backend env file."; exit 1; }
	@test "$(HOMOLOG_FRONTEND_ENV_FILE)" != "frontend/.env.production" || { echo "ERROR: homologation must not use the production frontend env file."; exit 1; }

# ── Deploy de homologação ────────────────────────────────────────────────────
.PHONY: deploy-homolog
deploy-homolog: deploy-backend-homolog deploy-frontend-homolog
	@echo "Deploy de homologação completo."

.PHONY: deploy-backend-homolog
deploy-backend-homolog: check-homolog-config docker-build-homolog docker-push-homolog cloud-run-deploy-homolog

.PHONY: docker-build-homolog
docker-build-homolog:
	@echo "Building homologation Docker image $(HOMOLOG_IMAGE)..."
	docker build --platform linux/amd64 -t $(HOMOLOG_IMAGE) backend/

.PHONY: docker-push-homolog
docker-push-homolog:
	@echo "Pushing homologation image to Artifact Registry..."
	docker push $(HOMOLOG_IMAGE)

.PHONY: cloud-run-deploy-homolog
cloud-run-deploy-homolog:
	@if [ ! -f $(HOMOLOG_BACKEND_ENV_FILE) ]; then \
		echo "ERROR: $(HOMOLOG_BACKEND_ENV_FILE) not found."; \
		exit 1; \
	fi
	gcloud run deploy $(HOMOLOG_SERVICE_NAME) \
		--image=$(HOMOLOG_IMAGE) \
		--region=$(GCP_REGION) \
		--platform=managed \
		--allow-unauthenticated \
		--set-env-vars="^|^$(shell grep -v '^[[:space:]]*#' $(HOMOLOG_BACKEND_ENV_FILE) | grep -v '^[[:space:]]*$$' | tr '\n' '|' | sed 's/|$$//')" \
		--set-secrets="DATABASE_URL=$(HOMOLOG_DATABASE_SECRET):latest,JWT_SECRET=$(HOMOLOG_JWT_SECRET):latest" \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT)

.PHONY: deploy-frontend-homolog
deploy-frontend-homolog: check-homolog-config frontend-build-homolog netlify-deploy-homolog

.PHONY: frontend-build-homolog
frontend-build-homolog:
	@if [ ! -f $(HOMOLOG_FRONTEND_ENV_FILE) ]; then \
		echo "ERROR: $(HOMOLOG_FRONTEND_ENV_FILE) not found."; \
		exit 1; \
	fi
	cd frontend && npm run build -- --mode homologation

.PHONY: netlify-deploy-homolog
netlify-deploy-homolog:
	cd frontend && netlify deploy --prod --no-build --dir=dist --site=$(HOMOLOG_NETLIFY_SITE)
	@echo "Homologation frontend URL: $(HOMOLOG_FRONTEND_URL)"

.PHONY: migrate-homolog
migrate-homolog:
	@if [ ! -f $(HOMOLOG_BACKEND_ENV_FILE) ]; then \
		echo "ERROR: $(HOMOLOG_BACKEND_ENV_FILE) not found."; \
		exit 1; \
	fi
	cd backend && set -a && . ../$(HOMOLOG_BACKEND_ENV_FILE) && set +a && poetry run alembic upgrade head

.PHONY: homolog-backend-url
homolog-backend-url:
	@gcloud run services describe $(HOMOLOG_SERVICE_NAME) \
		--region=$(GCP_REGION) \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT) \
		--format="value(status.url)"

.PHONY: logs-homolog
logs-homolog:
	gcloud logging read \
		"resource.type=cloud_run_revision AND resource.labels.service_name=$(HOMOLOG_SERVICE_NAME)" \
		--project=$(GCP_PROJECT) \
		--account=$(GCP_ACCOUNT) \
		--format="value(textPayload)" \
		--freshness=1h \
		--order=asc

# ── Console de conteúdo local com dados de homologação ───────────────────────
.PHONY: console-homolog
console-homolog:
	@scripts/console-homolog.sh

# ── Sincronização segura do catálogo para homologação ───────────────────────
.PHONY: sync-homolog-catalog-dry-run
sync-homolog-catalog-dry-run:
	@set -a; . backend/.env.production; set +a; \
	HOMOLOG_DB_PASSWORD=$$(security find-generic-password -s $(HOMOLOG_DB_KEYCHAIN) -a postgres -w); \
	$(SYNC_PYTHON) backend/scripts/sync_production_catalog_to_homolog.py \
		--production-database-url "$$DATABASE_URL" \
		--homologation-database-url "postgresql://postgres:$$HOMOLOG_DB_PASSWORD@db.$(HOMOLOG_SUPABASE_REF).supabase.co:5432/postgres"

.PHONY: sync-homolog-catalog-execute
sync-homolog-catalog-execute:
	@set -a; . backend/.env.production; set +a; \
	HOMOLOG_DB_PASSWORD=$$(security find-generic-password -s $(HOMOLOG_DB_KEYCHAIN) -a postgres -w); \
	$(SYNC_PYTHON) backend/scripts/sync_production_catalog_to_homolog.py \
		--production-database-url "$$DATABASE_URL" \
		--homologation-database-url "postgresql://postgres:$$HOMOLOG_DB_PASSWORD@db.$(HOMOLOG_SUPABASE_REF).supabase.co:5432/postgres" \
		--execute

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
	docker build --platform linux/amd64 -t $(IMAGE) backend/

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
		--set-env-vars="^|^$(shell grep -v '^[[:space:]]*#' backend/.env.production | grep -v '^[[:space:]]*$$' | tr '\n' '|' | sed 's/|$$//')" \
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
deploy-frontend: frontend-build netlify-deploy

.PHONY: frontend-build
frontend-build:
	@echo "Building frontend..."
	@if [ ! -f frontend/.env.production ]; then \
		echo "ERROR: frontend/.env.production not found."; \
		echo "Copy frontend/.env.production.example and set VITE_API_URL to the Cloud Run backend URL."; \
		echo "Tip: run 'make backend-url' to get the URL."; \
		exit 1; \
	fi
	cd frontend && npm run build

.PHONY: netlify-deploy
netlify-deploy:
	@echo "Deploying frontend to Netlify..."
	cd frontend && netlify deploy --prod --dir=dist --site=$(NETLIFY_SITE)
	@echo "Frontend URL: $(FRONTEND_URL)"

# ── Operação ──────────────────────────────────────────────────────────────────
.PHONY: logs
logs:
	gcloud logging read \
		"resource.type=cloud_run_revision AND resource.labels.service_name=$(SERVICE_NAME)" \
		--project=$(GCP_PROJECT) \
		--account=$(GCP_ACCOUNT) \
		--format="value(textPayload)" \
		--freshness=1h \
		--order=asc

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
	FRONTEND="$(FRONTEND_URL)"; \
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
	@echo "    make deploy-frontend     — só o frontend (Netlify)"
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

.PHONY: console-check-env
console-check-env:
	@echo "Validating console production environment..."
	@if [ ! -f console/.env.production ]; then \
		echo "ERROR: console/.env.production not found."; \
		echo "Copy console/.env.example and fill in production values."; \
		exit 1; \
	fi
	@for key in VITE_API_URL VITE_GOOGLE_CLIENT_ID VITE_ALLOWED_EMAIL_DOMAIN VITE_ENABLE_CONSOLE_LOCAL; do \
		grep -Eq "^$$key=.+" console/.env.production || { \
			echo "ERROR: $$key is missing or empty in console/.env.production."; \
			exit 1; \
		}; \
	done
	@grep -Eq '^VITE_ENABLE_CONSOLE_LOCAL=false$$' console/.env.production || { \
		echo "ERROR: VITE_ENABLE_CONSOLE_LOCAL must be false for production builds."; \
		exit 1; \
	}

.PHONY: console-build
console-build:
	@$(MAKE) console-check-env
	@echo "Building console..."
	cd console && npm run build

.PHONY: console-deploy
console-deploy: console-build
	@echo "Deploying console to Netlify..."
	cd console && netlify deploy --prod --dir=dist --site=$(CONSOLE_NETLIFY_SITE)

.PHONY: console-deploy-help
console-deploy-help:
	@echo "Console production order:"
	@echo "  1. Configure Google Auth Platform and backend/console variables."
	@echo "  2. make deploy-backend"
	@echo "  3. Run non-mutating smoke tests (/health, unauthenticated 401, corporate login)."
	@echo "  4. make console-deploy CONSOLE_NETLIFY_SITE=<site-id>"
