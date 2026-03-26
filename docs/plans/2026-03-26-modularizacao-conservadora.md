# Modularizacao Conservadora Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modularizar backend e frontend de forma conservadora, adicionar documentacao nas funcoes principais e criar testes unitarios e de integracao sem alterar o comportamento publico do sistema.

**Architecture:** O backend sera separado em `core`, `db`, `schemas`, `services` e `routers`, com `main.py` apenas compondo a aplicacao. O frontend sera reorganizado em `app`, `features` e `shared`, mantendo as rotas, telas e contratos HTTP atuais. Os testes serao adicionados por dominio primeiro no backend e depois no frontend.

**Tech Stack:** FastAPI, Pydantic, SQLite, pytest, pytest-asyncio, React, Vite, TypeScript, Vitest, Testing Library, MSW

---

### Task 1: Preparar estrutura de pastas do backend

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/services/__init__.py`

**Step 1: Write the failing test**

Nao se aplica. Esta tarefa cria estrutura sem comportamento.

**Step 2: Write minimal implementation**

Criar os diretorios e arquivos `__init__.py` vazios para suportar a modularizacao do backend.

**Step 3: Verify**

Run: `find backend/app -maxdepth 2 -type d | sort`
Expected: listar os novos diretorios `core`, `db`, `routers`, `schemas`, `services`

### Task 2: Extrair configuracao e banco do backend

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/database.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_database_setup.py`

**Step 1: Write the failing test**

Criar teste cobrindo:

- leitura de configuracao padrao;
- inicializacao de tabelas usando banco temporario;
- seed inicial de missoes.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_database_setup.py -v`
Expected: FAIL por modulos/funcoes ainda inexistentes

**Step 3: Write minimal implementation**

Extrair:

- env vars e constantes para `core/config.py`;
- `init_db` e helper de conexao para `db/database.py`;
- atualizar `main.py` para usar os novos modulos.

Adicionar docstrings nas funcoes publicas.

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_database_setup.py -v`
Expected: PASS

### Task 3: Extrair schemas do backend por dominio

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/users.py`
- Create: `backend/app/schemas/profile.py`
- Create: `backend/app/schemas/checklist.py`
- Create: `backend/app/schemas/comments.py`
- Create: `backend/app/schemas/notifications.py`
- Create: `backend/app/schemas/missions.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

Nao requer novo teste isolado. Usar os testes de importacao e integracao existentes/seguintes para proteger a extracao.

**Step 2: Write minimal implementation**

Mover os modelos Pydantic para arquivos separados por dominio e ajustar imports no backend.

Adicionar docstrings curtas quando fizer sentido em modelos menos obvios.

**Step 3: Verify**

Run: `cd backend && poetry run python -c "from app.main import app; print(app.title or 'ok')"`
Expected: comando executa sem erro de importacao

### Task 4: Extrair services de autenticacao e usuarios

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/services/user_service.py`
- Create: `backend/app/routers/health.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/routers/users.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/services/test_auth_service.py`
- Test: `backend/tests/services/test_user_service.py`
- Test: `backend/tests/integration/test_auth_routes.py`
- Test: `backend/tests/integration/test_user_routes.py`

**Step 1: Write the failing test**

Criar testes cobrindo:

- geracao e verificacao de OTP;
- criacao de usuario no primeiro login;
- leitura e atualizacao de usuario;
- contrato HTTP dos endpoints de auth e users.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/services/test_auth_service.py tests/services/test_user_service.py tests/integration/test_auth_routes.py tests/integration/test_user_routes.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Mover a regra de negocio para services e deixar os routers apenas como camada HTTP.

Preservar rotas existentes e respostas atuais.

Adicionar docstrings em services e handlers publicos.

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/services/test_auth_service.py tests/services/test_user_service.py tests/integration/test_auth_routes.py tests/integration/test_user_routes.py -v`
Expected: PASS

### Task 5: Extrair services de profile, checklist e comments

**Files:**
- Create: `backend/app/services/profile_service.py`
- Create: `backend/app/services/checklist_service.py`
- Create: `backend/app/services/comment_service.py`
- Create: `backend/app/routers/profile.py`
- Create: `backend/app/routers/checklist.py`
- Create: `backend/app/routers/comments.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/services/test_profile_service.py`
- Test: `backend/tests/services/test_checklist_service.py`
- Test: `backend/tests/services/test_comment_service.py`
- Test: `backend/tests/integration/test_profile_routes.py`
- Test: `backend/tests/integration/test_checklist_routes.py`
- Test: `backend/tests/integration/test_comment_routes.py`

**Step 1: Write the failing test**

Criar testes cobrindo:

- leitura e atualizacao de perfil;
- persistencia de checklist por usuario/fase/item;
- persistencia e leitura de comentarios publicos.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/services/test_profile_service.py tests/services/test_checklist_service.py tests/services/test_comment_service.py tests/integration/test_profile_routes.py tests/integration/test_checklist_routes.py tests/integration/test_comment_routes.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Extrair a logica para os services e criar routers dedicados.

Preservar formato das respostas da API.

Adicionar docstrings nas funcoes publicas.

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/services/test_profile_service.py tests/services/test_checklist_service.py tests/services/test_comment_service.py tests/integration/test_profile_routes.py tests/integration/test_checklist_routes.py tests/integration/test_comment_routes.py -v`
Expected: PASS

### Task 6: Extrair services de notifications e missions

**Files:**
- Create: `backend/app/services/notification_service.py`
- Create: `backend/app/services/mission_service.py`
- Create: `backend/app/routers/notifications.py`
- Create: `backend/app/routers/missions.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/services/test_notification_service.py`
- Test: `backend/tests/services/test_mission_service.py`
- Test: `backend/tests/integration/test_notification_routes.py`
- Test: `backend/tests/integration/test_mission_routes.py`

**Step 1: Write the failing test**

Criar testes cobrindo:

- leitura e marcacao de notificacoes;
- broadcast de notificacoes;
- leitura de missoes;
- completar/desfazer missao;
- leaderboard e pontos.

**Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/services/test_notification_service.py tests/services/test_mission_service.py tests/integration/test_notification_routes.py tests/integration/test_mission_routes.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Extrair a logica restante de `main.py`, mantendo os mesmos endpoints.

Adicionar docstrings nas funcoes publicas.

**Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/services/test_notification_service.py tests/services/test_mission_service.py tests/integration/test_notification_routes.py tests/integration/test_mission_routes.py -v`
Expected: PASS

### Task 7: Configurar framework de testes do frontend

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/server.ts`

**Step 1: Write the failing test**

Criar um teste simples de smoke para garantir que o runner esta configurado, por exemplo renderizacao basica do app/provider.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run`
Expected: FAIL por dependencias/configuracao ausentes

**Step 3: Write minimal implementation**

Instalar e configurar `vitest`, `jsdom`, `testing-library` e `msw`.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --run`
Expected: PASS no smoke test

### Task 8: Reorganizar a composicao global do frontend

**Files:**
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/app/providers/AuthProvider.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: imports dependentes
- Test: `frontend/src/app/App.test.tsx`

**Step 1: Write the failing test**

Criar teste cobrindo:

- renderizacao do login quando nao autenticado;
- renderizacao das rotas principais quando autenticado.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run frontend/src/app/App.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Mover provider e roteamento para `app/`, mantendo o comportamento atual.

Adicionar comentarios curtos onde a composicao nao for obvia.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --run frontend/src/app/App.test.tsx`
Expected: PASS

### Task 9: Reorganizar shared components e cliente HTTP

**Files:**
- Create: `frontend/src/shared/components/BottomNav.tsx`
- Create: `frontend/src/shared/components/TopBar.tsx`
- Create: `frontend/src/shared/components/ParrotMascot.tsx`
- Create: `frontend/src/shared/components/ProgressBar.tsx`
- Create: `frontend/src/shared/api/client.ts`
- Modify: imports dependentes
- Test: `frontend/src/shared/components/TopBar.test.tsx`

**Step 1: Write the failing test**

Criar teste de comportamento para `TopBar` com contagem de notificacoes mockada.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run frontend/src/shared/components/TopBar.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Mover componentes compartilhados e extrair cliente base HTTP usado pelos modulos de API.

Preservar comportamento e props atuais.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --run frontend/src/shared/components/TopBar.test.tsx`
Expected: PASS

### Task 10: Modularizar auth e trip no frontend

**Files:**
- Create: `frontend/src/features/auth/pages/LoginScreen.tsx`
- Create: `frontend/src/features/auth/services/auth-api.ts`
- Create: `frontend/src/features/trip/pages/HomeScreen.tsx`
- Create: `frontend/src/features/trip/pages/PhaseDetails.tsx`
- Create: `frontend/src/features/trip/pages/DayDetails.tsx`
- Create: `frontend/src/features/trip/data/tripData.ts`
- Modify: imports dependentes
- Test: `frontend/src/features/auth/LoginScreen.test.tsx`
- Test: `frontend/src/features/trip/PhaseDetails.test.tsx`
- Test: `frontend/src/features/trip/DayDetails.test.tsx`

**Step 1: Write the failing test**

Criar testes cobrindo:

- envio do telefone no login;
- carregamento de comentarios/checklist em `PhaseDetails`;
- carregamento de comentarios em `DayDetails`.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run frontend/src/features/auth/LoginScreen.test.tsx frontend/src/features/trip/PhaseDetails.test.tsx frontend/src/features/trip/DayDetails.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Mover os modulos de auth e trip para `features/`, mantendo rotas, chamadas de API e estrutura visual.

Adicionar comentarios curtos apenas nas partes menos obvias.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --run frontend/src/features/auth/LoginScreen.test.tsx frontend/src/features/trip/PhaseDetails.test.tsx frontend/src/features/trip/DayDetails.test.tsx`
Expected: PASS

### Task 11: Modularizar profile, missions e notifications no frontend

**Files:**
- Create: `frontend/src/features/profile/pages/ProfileScreen.tsx`
- Create: `frontend/src/features/profile/services/profile-api.ts`
- Create: `frontend/src/features/missions/pages/MissionsScreen.tsx`
- Create: `frontend/src/features/missions/services/missions-api.ts`
- Create: `frontend/src/features/notifications/pages/NotificationsScreen.tsx`
- Create: `frontend/src/features/notifications/services/notifications-api.ts`
- Modify: imports dependentes
- Test: `frontend/src/features/profile/ProfileScreen.test.tsx`
- Test: `frontend/src/features/missions/MissionsScreen.test.tsx`
- Test: `frontend/src/features/notifications/NotificationsScreen.test.tsx`

**Step 1: Write the failing test**

Criar testes cobrindo:

- carregamento e salvamento de perfil;
- carregamento e toggle de missoes;
- carregamento e marcacao de notificacoes.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --run frontend/src/features/profile/ProfileScreen.test.tsx frontend/src/features/missions/MissionsScreen.test.tsx frontend/src/features/notifications/NotificationsScreen.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Mover os modulos para `features/` com servicos de API separados por dominio.

Preservar chamadas e comportamento atuais.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --run frontend/src/features/profile/ProfileScreen.test.tsx frontend/src/features/missions/MissionsScreen.test.tsx frontend/src/features/notifications/NotificationsScreen.test.tsx`
Expected: PASS

### Task 12: Modularizar telas estaticas restantes do frontend

**Files:**
- Create: `frontend/src/features/documents/pages/DocumentsScreen.tsx`
- Create: `frontend/src/features/recommendations/pages/RecommendationsScreen.tsx`
- Create: `frontend/src/features/emergency/pages/EmergencyContacts.tsx`
- Create: `frontend/src/features/sharing/pages/SharingXPScreen.tsx`
- Modify: imports dependentes

**Step 1: Write the failing test**

Nao requer novo teste prioritario nesta etapa. Esta migracao e estrutural e sera coberta pelos testes de app/router.

**Step 2: Write minimal implementation**

Mover as telas restantes para `features/` e ajustar imports.

**Step 3: Verify**

Run: `cd frontend && npm run build`
Expected: build concluido com sucesso

### Task 13: Executar verificacoes finais

**Files:**
- Verify only

**Step 1: Run backend tests**

Run: `cd backend && poetry run pytest -v`
Expected: todos os testes backend passando

**Step 2: Run frontend tests**

Run: `cd frontend && npm test -- --run`
Expected: todos os testes frontend passando

**Step 3: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: sem erros

**Step 4: Run frontend build**

Run: `cd frontend && npm run build`
Expected: build concluido com sucesso

**Step 5: Smoke import for backend**

Run: `cd backend && poetry run python -c "from app.main import app; print('ok')"`
Expected: `ok`
