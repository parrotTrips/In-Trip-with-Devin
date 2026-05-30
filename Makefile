# ── Configuração ──────────────────────────────────────────────────────────────
GCP_PROJECT    = jogo-da-vida-497700
GCP_ACCOUNT    = angelo@parrottrips.com
GCP_REGION     = southamerica-east1
SERVICE_NAME   = parrot-trips-backend
IMAGE_REPO     = $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/parrot-trips/backend
GCS_BUCKET       = parrot-trips-frontend
FRONTEND_URL     = https://storage.googleapis.com/$(GCS_BUCKET)

# Image tag: uses short git commit hash by default
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
deploy-frontend: frontend-build gcs-upload

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

.PHONY: gcs-upload
gcs-upload:
	@echo "Uploading frontend to Cloud Storage..."
	gcloud storage cp -r frontend/dist/* gs://$(GCS_BUCKET)/ \
		--account=$(GCP_ACCOUNT) \
		--project=$(GCP_PROJECT)
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
