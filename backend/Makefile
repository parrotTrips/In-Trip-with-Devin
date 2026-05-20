PYTHON = env/bin/python
PIP    = env/bin/pip
PYTEST = env/bin/pytest
UV     = env/bin/uvicorn
PORT   = 8000

# ── servidor ───────────────────────────────────────────────────────────────────
dev:
	@echo "Subindo backend na porta $(PORT)..."
	@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	$(UV) app.main:app --port $(PORT) --reload

stop:
	@pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Backend parado." || echo "Nenhum processo rodando."

# ── testes ─────────────────────────────────────────────────────────────────────
test:
	$(PYTEST) tests/ -v

test-watch:
	$(PYTEST) tests/ -v --tb=short -x

test-middleware:
	$(PYTEST) tests/integration/test_jwt_middleware.py -v

# ── e2e ────────────────────────────────────────────────────────────────────────
e2e:
	@if [ -z "$(PHONE)" ]; then \
		echo "Uso: make e2e PHONE=+5511999999999"; \
		exit 1; \
	fi
	$(PYTHON) tests/e2e/test_opcao1_whatsapp_otp.py $(PHONE)

# ── banco de dados ─────────────────────────────────────────────────────────────
migrate:
	env/bin/alembic upgrade head

migrate-status:
	env/bin/alembic current

# ── utilitários ────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt 2>/dev/null || $(PIP) install -e ".[dev]" 2>/dev/null || true

kill-port:
	@lsof -ti:$(PORT) | xargs kill -9 2>/dev/null && echo "Porta $(PORT) liberada." || echo "Porta $(PORT) ja estava livre."

.PHONY: dev stop test test-watch test-middleware e2e migrate migrate-status install kill-port
