# Content Console Production Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publicar a fatia A do console com Google Workspace SSO, operações seguras e salvamento transacional, sem alterar o comportamento de autenticação do app do viajante.

**Architecture:** O `/console` deixa de ser validado pelo JWT interno e passa a ter uma dependência Google aplicada ao router inteiro. O console React guarda o Google ID token em `sessionStorage` e o envia por um cliente HTTP central. As edições de fase, checklist e links são gravadas por um endpoint atômico e fases publicadas são imutáveis até serem despublicadas.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL, `google-auth`, CacheControl, React 18, TypeScript, Vite, `@react-oauth/google`, Vitest e Pytest.

**Design:** `docs/plans/2026-09-22-content-console-production-hardening-design.md`

---

## Regras para execução

- Usar TDD em cada tarefa: escrever o teste, vê-lo falhar pelo motivo esperado, implementar o mínimo e rodar novamente.
- Não editar os arquivos modificados e não relacionados em `frontend/src/features/team/` nem `resume.txt`.
- Não executar deploy nem alterar dados de produção durante a implementação.
- Não remover o JWT interno, o OTP de WhatsApp ou a compatibilidade de `/admin` com Apps Script.
- Não registrar Google ID tokens, nem mesmo em testes de erro.
- Não criar migration: este trabalho usa o schema atual.
- Antes de afirmar conclusão, usar `superpowers:verification-before-completion`.

### Task 1: Configuração e validador Google no backend

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/core/console_auth.py`
- Create: `backend/tests/core/test_console_auth.py`
- Modify: `backend/tests/conftest.py`
- Modify: `backend/pyproject.toml`
- Modify mechanically: `backend/poetry.lock`

**Step 1: Escrever testes de configuração e claims**

Criar `backend/tests/core/test_console_auth.py`. Os testes devem chamar a dependência diretamente com credenciais HTTP simuladas e substituir `_verify_google_token_sync`, sem acessar a rede.

Casos obrigatórios:

```python
def test_missing_bearer_returns_401(...): ...
def test_missing_server_configuration_returns_503(...): ...
def test_valid_workspace_claims_return_principal(...): ...
def test_invalid_google_token_returns_401(...): ...
def test_email_not_verified_returns_403(...): ...
def test_wrong_email_domain_returns_403(...): ...
def test_missing_or_wrong_hd_returns_403(...): ...
def test_missing_sub_returns_403(...): ...
def test_local_bypass_requires_development_and_flag(...): ...
def test_local_bypass_never_works_in_production(...): ...
def test_raw_token_is_absent_from_logs_and_error(..., capsys): ...
```

Use claims válidos comuns:

```python
VALID_CLAIMS = {
    "sub": "google-user-123",
    "email": "pessoa@parrottrips.com",
    "email_verified": True,
    "hd": "parrottrips.com",
}
```

Antes de cada teste, configure explicitamente `APP_ENV`, `ENABLE_CONSOLE_LOCAL`, `GOOGLE_OAUTH_CLIENT_ID` e `ALLOWED_EMAIL_DOMAIN` com `monkeypatch`. Não deixe os testes dependerem do `.env` da máquina.

**Step 2: Rodar os testes e confirmar a falha**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/core/test_console_auth.py -q
```

Expected: FAIL porque `app.core.console_auth` ainda não existe.

**Step 3: Adicionar configuração explícita**

Em `backend/app/core/config.py`, adicionar funções que leem o ambiente no momento de uso, facilitando isolamento dos testes:

```python
def get_app_env() -> str:
    return os.environ.get("APP_ENV", "development").strip().lower()


def console_local_bypass_enabled() -> bool:
    return (
        get_app_env() == "development"
        and os.environ.get("ENABLE_CONSOLE_LOCAL", "false").strip().lower() == "true"
    )


def get_google_oauth_client_id() -> str:
    return os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()


def get_allowed_email_domain() -> str:
    return os.environ.get("ALLOWED_EMAIL_DOMAIN", "").strip().lower()


def get_cors_allowed_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,https://parrot-trips.netlify.app",
    )
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
```

**Step 4: Implementar a dependência Google**

Criar `backend/app/core/console_auth.py` com:

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache

import cachecontrol
import requests
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import (
    console_local_bypass_enabled,
    get_allowed_email_domain,
    get_google_oauth_client_id,
)
from app.core.logger import log_erro

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    uid: str
    email: str


class _TimeoutRequest(Request):
    def __call__(self, *args, timeout=10, **kwargs):
        return super().__call__(*args, timeout=timeout, **kwargs)


@lru_cache(maxsize=1)
def _google_request() -> Request:
    session = cachecontrol.CacheControl(requests.Session())
    return _TimeoutRequest(session=session)


def _verify_google_token_sync(token: str, audience: str) -> dict:
    return id_token.verify_oauth2_token(
        token,
        _google_request(),
        audience=audience,
        clock_skew_in_seconds=10,
    )


def _validate_workspace_claims(claims: dict, domain: str) -> AuthenticatedPrincipal:
    email = claims.get("email")
    sub = claims.get("sub")
    if (
        claims.get("email_verified") is not True
        or not isinstance(email, str)
        or email.lower().rsplit("@", 1)[-1] != domain
        or claims.get("hd") != domain
        or not isinstance(sub, str)
        or not sub.strip()
    ):
        raise HTTPException(status_code=403, detail="Google Workspace account not authorized")
    return AuthenticatedPrincipal(uid=sub, email=email.lower())


async def require_console_access(
    credentials: HTTPAuthorizationCredentials | None = None,
) -> AuthenticatedPrincipal:
    # Na implementação final, credentials deve vir de Depends(_bearer); os testes
    # podem chamar a função diretamente.
    if console_local_bypass_enabled():
        return AuthenticatedPrincipal(uid="local-console", email="local@parrottrips.com")

    audience = get_google_oauth_client_id()
    domain = get_allowed_email_domain()
    if not audience or not domain:
        raise HTTPException(status_code=503, detail="Console authentication is not configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        claims = await asyncio.to_thread(
            _verify_google_token_sync, credentials.credentials, audience
        )
    except (ValueError, google_auth_exceptions.GoogleAuthError):
        raise HTTPException(status_code=401, detail="Unauthorized") from None
    except Exception as exc:
        log_erro("console_google_auth_failure", error_type=type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to validate authentication") from None
    return _validate_workspace_claims(claims, domain)
```

Ao escrever a versão real, declarar `credentials` com `Depends(_bearer)`. Não incluir o token em exceções ou logs.

**Step 5: Adicionar dependência e atualizar o lock**

Adicionar `cachecontrol = "^0.14.3"` a `backend/pyproject.toml`. `requests` já é dependência transitiva de `google-auth`; se o Poetry exigir declaração direta, adicionar `requests = "^2.32.0"`.

Run:

```bash
cd backend && poetry lock
```

Expected: `poetry.lock` atualizado sem alterar versões não relacionadas além do necessário.

**Step 6: Atualizar limpeza de módulos dos testes**

Adicionar `app.core.console_auth` ao `MODULES_TO_CLEAR` de `backend/tests/conftest.py` e configurar valores seguros por padrão no fixture `client`:

```python
monkeypatch.setenv("APP_ENV", "development")
monkeypatch.setenv("ENABLE_CONSOLE_LOCAL", "true")
monkeypatch.setenv("ALLOWED_EMAIL_DOMAIN", "parrottrips.com")
```

Os testes específicos de autenticação devem sobrescrever esses valores explicitamente.

**Step 7: Rodar os testes**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/core/test_console_auth.py -q
```

Expected: todos passam e nenhuma saída contém o token sentinela usado no teste.

**Step 8: Commit**

```bash
git add backend/app/core/config.py backend/app/core/console_auth.py \
  backend/tests/core/test_console_auth.py backend/tests/conftest.py \
  backend/pyproject.toml backend/poetry.lock
git commit -m "feat(console): validate Google Workspace identity tokens"
```

### Task 2: Proteger o router inteiro sem regredir o JWT atual

**Files:**
- Modify: `backend/app/middleware/auth.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/integration/test_console_routes.py`
- Modify: `backend/tests/integration/test_jwt_middleware.py`
- Create: `backend/tests/integration/test_runtime_security.py`

**Step 1: Substituir os helpers de login nos testes do console**

Em `backend/tests/integration/test_console_routes.py`, remova o seed de usuário admin e o helper OTP `_auth`. Os testes do CRUD devem usar o bypass local do fixture `client`; para provar proteção real, crie testes separados com o bypass desligado e `_verify_google_token_sync` mockado.

Adicionar testes que provem:

```python
def test_every_console_route_rejects_missing_google_token(...): ...
def test_console_accepts_valid_google_workspace_token(...): ...
def test_console_does_not_query_users_table_for_access(...): ...
```

O primeiro deve exercitar ao menos `GET /console/trips`, uma rota de fase e uma rota de mutação; todas devem falhar antes do serviço.

**Step 2: Adicionar testes de regressão do middleware JWT**

Em `backend/tests/integration/test_jwt_middleware.py`, preservar os casos existentes e adicionar:

```python
def test_console_is_not_parsed_as_internal_jwt(...): ...
def test_profile_still_rejects_google_like_token(...): ...
```

**Step 3: Rodar e confirmar a falha**

Run:

```bash
cd backend && .venv/bin/python -m pytest \
  tests/integration/test_console_routes.py \
  tests/integration/test_jwt_middleware.py -q
```

Expected: FAIL porque o middleware legado ainda intercepta `/console` e o router ainda chama `require_admin`.

**Step 4: Isolar os dois sistemas de autenticação**

Em `backend/app/middleware/auth.py`, adicionar `/console` aos prefixos ignorados pelo JWT interno e renomear/comentar a constante para explicitar que a autenticação continua no router:

```python
_INTERNAL_JWT_BYPASS_PREFIXES = ("/auth", "/admin", "/console")
```

Em `backend/app/routers/console.py`:

```python
from app.core.console_auth import require_console_access

router = APIRouter(
    prefix="/console",
    tags=["console"],
    dependencies=[Depends(require_console_access)],
)
```

Remover todas as chamadas individuais a `require_admin` e o parâmetro `request` que só existia para elas. Remover `require_admin` de `backend/app/services/console_service.py`.

**Step 5: Configurar CORS e documentação por ambiente**

Em `backend/app/main.py`, construir o FastAPI assim:

```python
is_development = get_app_env() == "development"
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if is_development else None,
    redoc_url="/redoc" if is_development else None,
    openapi_url="/openapi.json" if is_development else None,
)
```

Configurar CORS com `get_cors_allowed_origins()`, `allow_credentials=False`, métodos explícitos necessários (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`) e headers `Authorization` e `Content-Type`.

Garanta pela ordem dos middlewares que respostas 401/403 também recebam headers CORS. O teste deve validar o comportamento, não apenas a ordem das linhas.

**Step 6: Testar segurança de runtime**

Criar `backend/tests/integration/test_runtime_security.py` para validar:

- `/health` público;
- docs/OpenAPI presentes em development e ausentes em production;
- preflight da origem permitida;
- origem não permitida sem `Access-Control-Allow-Origin`;
- resposta 401 do console com CORS para origem permitida.

**Step 7: Rodar os testes focados**

Run:

```bash
cd backend && .venv/bin/python -m pytest \
  tests/integration/test_console_routes.py \
  tests/integration/test_jwt_middleware.py \
  tests/integration/test_runtime_security.py -q
```

Expected: PASS.

**Step 8: Commit**

```bash
git add backend/app/middleware/auth.py backend/app/routers/console.py \
  backend/app/services/console_service.py backend/app/main.py \
  backend/tests/integration/test_console_routes.py \
  backend/tests/integration/test_jwt_middleware.py \
  backend/tests/integration/test_runtime_security.py
git commit -m "feat(console): protect all routes with Google SSO"
```

### Task 3: Criar salvamento atômico e regras de fase publicada

**Files:**
- Modify: `backend/app/schemas/console.py`
- Modify: `backend/app/services/console_service.py`
- Modify: `backend/app/routers/console.py`
- Modify: `backend/tests/integration/test_console_routes.py`

**Step 1: Escrever testes de validação e imutabilidade**

Adicionar testes para:

```python
def test_published_phase_cannot_be_patched(...): ...
def test_published_phase_checklist_cannot_be_replaced(...): ...
def test_published_phase_links_cannot_be_replaced(...): ...
def test_published_phase_cannot_be_deleted(...): ...
def test_reordering_published_phases_is_rejected(...): ...
def test_empty_title_or_description_is_rejected(...): ...
def test_invalid_link_scheme_is_rejected(...): ...
def test_end_before_start_is_rejected(...): ...
```

Use status 409 para tentativa de mutar fase publicada e 422 para payload inválido.

**Step 2: Escrever testes do endpoint atômico**

Contrato:

```http
PUT /console/phases/{phase_id}/content
Content-Type: application/json

{
  "title": "Documentos",
  "subtitle": null,
  "icon": "passport",
  "short_description": "Prepare seus documentos",
  "detailed_description": "...",
  "starts_at": null,
  "ends_at": null,
  "checklist": [{"label": "Passaporte", "is_required": true}],
  "links": [{"label": "Portal", "url": "https://example.com"}]
}
```

Adicionar:

```python
def test_atomic_save_updates_phase_and_children(...): ...
def test_atomic_save_rolls_everything_back_on_child_failure(...): ...
```

Para o rollback, force uma exceção depois do `UPDATE` e antes do commit por meio de um helper interno monkeypatchável ou de uma violação controlada. Depois, abra uma nova sessão e confirme que título, checklist e links originais permanecem intactos.

**Step 3: Rodar e confirmar a falha**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q
```

Expected: FAIL porque não há endpoint atômico nem bloqueio de publicados.

**Step 4: Fortalecer schemas**

Em `backend/app/schemas/console.py`, usar `Field(min_length=1)` e `HttpUrl`, normalizar whitespace e validar datas com `model_validator`. Criar:

```python
class PhaseContentUpdate(BaseModel):
    title: str = Field(min_length=1)
    subtitle: str | None = None
    icon: str | None = None
    short_description: str = Field(min_length=1)
    detailed_description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    checklist: list[ChecklistItemIn] = Field(default_factory=list)
    links: list[LinkIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at must not be earlier than starts_at")
        return self
```

Trocar defaults mutáveis `=[]` por `Field(default_factory=list)` nos schemas existentes.

**Step 5: Centralizar a guarda de rascunho**

Criar helper no service:

```python
async def require_draft_phase(session: AsyncSession, phase_id: str) -> None:
    visible = await session.scalar(
        text("SELECT is_visible FROM trip_phases WHERE id = CAST(:p AS uuid)"),
        {"p": phase_id},
    )
    if visible is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    if visible:
        raise HTTPException(status_code=409, detail="Unpublish the phase before changing it")
```

Usá-lo em `update_phase`, `replace_checklist`, `replace_links`, `delete_phase` e no novo salvamento atômico. Para reordenação, rejeitar se qualquer fase afetada estiver publicada.

**Step 6: Implementar uma única transação**

Criar `save_phase_content(session, phase_id, data)`. A função deve:

1. verificar que a fase existe e é rascunho;
2. atualizar os campos da fase;
3. apagar progresso dos itens antigos;
4. substituir checklist;
5. substituir links;
6. executar apenas um `session.commit()` no final;
7. fazer `session.rollback()` e relançar em qualquer exceção.

Não chamar os helpers atuais que fazem commit individual. Extraia helpers privados sem commit se precisar evitar duplicação.

Adicionar rota:

```python
@router.put("/phases/{phase_id}/content")
async def save_phase_content_handler(
    phase_id: str,
    body: PhaseContentUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    return await save_phase_content(session, phase_id, body.model_dump(mode="json"))
```

**Step 7: Rodar testes focados**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/integration/test_console_routes.py -q
```

Expected: PASS.

**Step 8: Commit**

```bash
git add backend/app/schemas/console.py backend/app/services/console_service.py \
  backend/app/routers/console.py backend/tests/integration/test_console_routes.py
git commit -m "feat(console): save draft phase content atomically"
```

### Task 4: Substituir OTP por sessão Google no console

**Files:**
- Modify: `console/package.json`
- Modify mechanically: `console/package-lock.json`
- Modify: `console/src/vite-env.d.ts`
- Create: `console/src/config.ts`
- Create: `console/src/auth/google-session.ts`
- Modify: `console/src/auth/auth-context.ts`
- Modify: `console/src/auth/AuthProvider.tsx`
- Modify: `console/src/auth/LoginScreen.tsx`
- Modify: `console/src/App.tsx`
- Replace tests: `console/src/auth/LoginScreen.test.tsx`
- Modify tests: `console/src/auth/AuthProvider.test.tsx`
- Create: `console/src/auth/google-session.test.ts`
- Create: `console/src/config.test.ts`

**Step 1: Instalar o componente oficial do frontend**

Run:

```bash
cd console && npm install @react-oauth/google
```

Expected: `package.json` e `package-lock.json` atualizados.

**Step 2: Escrever testes de configuração e sessão**

Testar:

- produção bloqueada sem `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID` ou domínio;
- client ID precisa terminar em `.apps.googleusercontent.com`;
- domínio esperado é `parrottrips.com`;
- token válido é restaurado do `sessionStorage`;
- token expirado, malformado ou de domínio diferente é removido;
- nada é lido ou escrito em `localStorage`;
- bypass frontend exige `import.meta.env.DEV` e `VITE_ENABLE_CONSOLE_LOCAL=true`.

Use um helper de teste para criar JWTs sem assinatura, pois essa decodificação serve somente para UX:

```typescript
function fakeJwt(payload: object) {
  const encode = (value: object) => btoa(JSON.stringify(value))
    .replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
  return `${encode({ alg: 'none' })}.${encode(payload)}.`;
}
```

**Step 3: Rodar e confirmar a falha**

Run:

```bash
cd console && npm run test -- src/auth/google-session.test.ts src/config.test.ts
```

Expected: FAIL porque os módulos ainda não existem.

**Step 4: Implementar configuração fail-closed**

Em `console/src/config.ts`, exportar um resultado discriminado:

```typescript
export type ConsoleConfig = {
  apiUrl: string;
  googleClientId: string;
  allowedEmailDomain: string;
  localBypass: boolean;
};

export function readConfig(): { ok: true; value: ConsoleConfig } | { ok: false; error: string } {
  // Validar URL absoluta, Client ID, domínio e bypass duplamente guardado.
}
```

Em produção, nunca usar `http://localhost:8000` como fallback silencioso.

**Step 5: Implementar armazenamento e restauração**

Em `console/src/auth/google-session.ts`:

```typescript
export const GOOGLE_CREDENTIAL_KEY = 'parrot_console_google_credential';

export type GooglePrincipal = {
  sub: string;
  email: string;
  credential: string;
  expiresAt: number;
};

export function acceptCredential(credential: string, domain: string): GooglePrincipal | null;
export function restoreCredential(domain: string): GooglePrincipal | null;
export function currentCredential(): string | null;
export function clearCredentialIfCurrent(expected: string): boolean;
export function clearCredential(): void;
export function subscribeSession(listener: () => void): () => void;
```

`acceptCredential` valida superficialmente `sub`, `email`, domínio e `exp`, grava apenas em `sessionStorage` e notifica listeners. `clearCredentialIfCurrent` compara o valor atual antes de remover.

**Step 6: Reescrever AuthProvider e LoginScreen**

`AuthProvider` mantém `GooglePrincipal | null`, restaura a sessão na inicialização e assina mudanças do store. Remover `AuthUser`, OTP, telefone e qualquer referência a `parrot_console_user`.

`LoginScreen` usa:

```tsx
<GoogleLogin
  hosted_domain={config.allowedEmailDomain}
  onSuccess={(response) => response.credential && login(response.credential)}
  onError={() => setError('Não foi possível entrar com o Google.')}
/>
```

O domínio do frontend continua sendo UX; o backend é a autoridade.

**Step 7: Montar provider e gate de configuração**

Em `App.tsx`, se a configuração for inválida, renderizar uma tela bloqueada. Caso contrário:

```tsx
<GoogleOAuthProvider clientId={config.googleClientId}>
  <AuthProvider config={config}>
    <BrowserRouter>{/* rotas */}</BrowserRouter>
  </AuthProvider>
</GoogleOAuthProvider>
```

O bypass local pode fornecer um principal local apenas quando as duas guardas frontend forem verdadeiras; ele nunca deve inventar um Google token em build de produção.

**Step 8: Rodar testes e build**

Run:

```bash
cd console && npm run test -- src/auth src/config.test.ts && npm run build
```

Expected: PASS e build limpo.

**Step 9: Commit**

```bash
git add console/package.json console/package-lock.json console/src/vite-env.d.ts \
  console/src/config.ts console/src/config.test.ts console/src/auth console/src/App.tsx
git commit -m "feat(console): sign in with Google Workspace"
```

### Task 5: Tornar o cliente HTTP seguro contra expiração e concorrência

**Files:**
- Modify: `console/src/api/client.ts`
- Modify: `console/src/api/console-api.ts`
- Create: `console/src/api/client.test.ts`
- Modify: `console/src/auth/AuthProvider.test.tsx`

**Step 1: Escrever testes do cliente**

Cobrir:

```typescript
test('adds the current Google credential as Bearer', ...)
test('401 clears the credential used by that request', ...)
test('a delayed 401 cannot clear a newer credential', ...)
test('403 preserves the session and exposes an authorization message', ...)
test('503 preserves the session and exposes a configuration message', ...)
test('network and non-json errors are sanitized', ...)
```

O teste concorrente deve iniciar request A com token antigo, aceitar token novo, então resolver A com 401 e confirmar que o novo token permanece.

**Step 2: Rodar e confirmar a falha**

Run:

```bash
cd console && npm run test -- src/api/client.test.ts
```

Expected: FAIL porque o cliente ainda lê `localStorage` e não protege concorrência.

**Step 3: Reescrever o cliente central**

O `request` deve capturar a credencial no começo:

```typescript
const credential = currentCredential();
const response = await fetch(...);
if (response.status === 401 && credential) {
  clearCredentialIfCurrent(credential);
}
```

Criar `ApiError` com `status` e mensagem amigável. Não incluir token, headers completos ou resposta bruta na mensagem.

**Step 4: Adicionar operação atômica à API**

Em `console/src/api/console-api.ts`, criar:

```typescript
export type PhaseContentInput = {
  title: string;
  subtitle: string | null;
  icon: string | null;
  short_description: string;
  detailed_description: string | null;
  starts_at: string | null;
  ends_at: string | null;
  checklist: { label: string; is_required: boolean }[];
  links: { label: string; url: string }[];
};

export function savePhaseContent(phaseId: string, body: PhaseContentInput) {
  return request<{ id: string; updated: boolean }>(
    `/console/phases/${phaseId}/content`,
    { method: 'PUT', body: JSON.stringify(body) },
  );
}
```

**Step 5: Rodar testes**

Run:

```bash
cd console && npm run test -- src/api/client.test.ts src/auth/AuthProvider.test.tsx
```

Expected: PASS.

**Step 6: Commit**

```bash
git add console/src/api/client.ts console/src/api/client.test.ts \
  console/src/api/console-api.ts console/src/auth/AuthProvider.test.tsx
git commit -m "feat(console): handle Google session expiry safely"
```

### Task 6: Endurecer criação, edição, publicação e exclusão na interface

**Files:**
- Modify: `console/src/pages/TripsScreen.tsx`
- Modify: `console/src/pages/TripsScreen.test.tsx`
- Modify: `console/src/pages/PhasesScreen.tsx`
- Modify: `console/src/pages/PhasesScreen.test.tsx`
- Modify: `console/src/pages/PhaseEditor.tsx`
- Modify: `console/src/pages/PhaseEditor.test.tsx`

**Step 1: Escrever testes de UX segura**

Adicionar casos:

- aviso persistente sobre o import legado;
- criação exige título e descrição curta não vazios;
- fase publicada não oferece edição, subida ou exclusão;
- abrir URL do editor de fase publicada mostra somente leitura e instrução para despublicar;
- exclusão de rascunho abre confirmação e exige o título exato;
- cancelar confirmação não chama a API;
- controles ficam desabilitados durante requests;
- editor faz somente um `PUT /content` ao salvar;
- URL inválida e datas invertidas são rejeitadas antes do request;
- falha mantém os dados preenchidos e mostra mensagem;
- sucesso mostra confirmação clara.

**Step 2: Rodar e confirmar a falha**

Run:

```bash
cd console && npm run test -- \
  src/pages/TripsScreen.test.tsx \
  src/pages/PhasesScreen.test.tsx \
  src/pages/PhaseEditor.test.tsx
```

Expected: FAIL nos novos cenários.

**Step 3: Adicionar aviso operacional**

Na tela de viagens e/ou fases, renderizar aviso visível:

> Não importe esta viagem pela planilha depois de editá-la aqui. O import legado pode substituir fases, checklist e links.

Não afirmar que existe detecção automática de último import, pois o banco não possui esse dado.

**Step 4: Implementar criação validada**

Trocar o botão que cria imediatamente `Nova fase` com descrição vazia por um formulário/modal simples com título e descrição curta. Bloquear submit vazio e impedir duplo clique durante request.

**Step 5: Implementar estado publicado somente leitura**

Em `PhasesScreen`:

- publicar/despublicar continua disponível;
- editar, subir e excluir ficam indisponíveis para fase publicada;
- se qualquer fase estiver publicada, desabilitar reordenação da lista e explicar por quê.

Em `PhaseEditor`, manter a rota acessível para leitura, mas desabilitar campos e salvar quando `is_visible` for verdadeiro.

**Step 6: Implementar confirmação de exclusão**

Usar um dialog acessível controlado por estado. Exigir que o texto digitado seja exatamente `phase.title`. Não usar apenas `window.confirm`, porque ele não permite confirmar o alvo por nome.

**Step 7: Trocar três requests por um**

No `save` de `PhaseEditor`, chamar somente `savePhaseContent`. Validar no cliente:

- `title.trim()` e `short_description.trim()` não vazios;
- links com `http:` ou `https:` e URL parseável;
- fim não anterior ao início.

O backend continua sendo a validação confiável.

**Step 8: Rodar testes e build**

Run:

```bash
cd console && npm run test && npm run build
```

Expected: toda a suíte do console passa e TypeScript/build terminam sem erro.

**Step 9: Commit**

```bash
git add console/src/pages
git commit -m "feat(console): guard published and destructive content changes"
```

### Task 7: Documentar configuração, deploy e rollback

**Files:**
- Create: `console/.env.example`
- Modify: `README.md`
- Modify: `PLATAFORMA_CONTEUDO.md`
- Modify: `TRABALHO_2026-09-21.md`
- Modify: `Makefile`

**Step 1: Escrever o exemplo de ambiente**

`console/.env.example`:

```env
VITE_API_URL=https://your-cloud-run-service.run.app
VITE_GOOGLE_CLIENT_ID=000000000000-example.apps.googleusercontent.com
VITE_ALLOWED_EMAIL_DOMAIN=parrottrips.com
VITE_ENABLE_CONSOLE_LOCAL=false
```

**Step 2: Documentar Google Auth Platform**

No README, explicar:

- OAuth Client do tipo Web application;
- audience Internal, se disponível no Workspace;
- origem JavaScript do console;
- ausência de redirect URI e client secret;
- mesmo Client ID no backend e frontend;
- variáveis obrigatórias;
- `CORS_ALLOWED_ORIGINS` deve preservar a origem do app do viajante;
- bypass local duplamente guardado.

**Step 3: Atualizar documentos de acompanhamento**

Atualizar `PLATAFORMA_CONTEUDO.md` e `TRABALHO_2026-09-21.md` para remover instruções de OTP/admin no banco e registrar que o acesso agora é por qualquer conta válida `@parrottrips.com`.

Não reescrever o histórico do relatório: marcar o usuário admin fictício como legado/não utilizado pelo novo console.

**Step 4: Adicionar validação de deploy**

No `Makefile`, fazer `console-build` verificar as variáveis necessárias para build de produção e manter o comando de deploy existente. Não inserir valores reais no repositório.

Adicionar comentários/targets de ajuda para a ordem:

1. configurar Google e variáveis;
2. `make deploy-backend`;
3. smoke tests sem mutação;
4. `make console-deploy`.

**Step 5: Revisar documentação**

Run:

```bash
rg -n "WhatsApp|OTP|role.?admin|parrot_console_user|VITE_DEV_AUTO_LOGIN" \
  README.md PLATAFORMA_CONTEUDO.md TRABALHO_2026-09-21.md console backend/app
```

Expected: ocorrências restantes são históricas ou pertencem ao app do viajante; nenhuma instrução ativa do console depende de OTP/admin no banco.

**Step 6: Commit**

```bash
git add console/.env.example README.md PLATAFORMA_CONTEUDO.md \
  TRABALHO_2026-09-21.md Makefile
git commit -m "docs(console): document Google SSO deployment"
```

### Task 8: Verificação integral e handoff de produção

**Files:**
- Modify only if verification exposes a scoped defect.

**Step 1: Rodar suíte completa do backend**

Run:

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
```

Expected: todos os testes passam. Se a falha histórica `test_activity_checkins_table_metadata` ainda existir, confirme que ela também falha no commit-base e registre separadamente; não esconda nenhuma falha nova.

**Step 2: Rodar suíte e build do console**

Run:

```bash
cd console && npm run test && npm run build
```

Expected: PASS e `dist/` criado.

**Step 3: Verificar regressão do frontend do viajante**

Run:

```bash
cd frontend && npm run test -- --run
```

Se o script do projeto usar sintaxe diferente, consultar `frontend/package.json` e executar o equivalente não interativo. Expected: nenhuma regressão causada por backend/auth.

**Step 4: Fazer revisão de segurança local**

Verificar:

```bash
rg -n "console\.log|credential|Authorization|GOOGLE_OAUTH_CLIENT_ID|CLIENT_SECRET" \
  backend/app/core/console_auth.py console/src
```

Expected: nenhum log de token, nenhum client secret e nenhuma credencial real versionada.

**Step 5: Fazer smoke test local sem mutação**

Com bypass local duplamente habilitado:

- abrir lista de viagens;
- abrir lista e detalhe de fases;
- confirmar que fase publicada está somente leitura;
- confirmar que request sem bypass/token recebe 401;
- não salvar, publicar, despublicar ou excluir conteúdo ligado a produção.

**Step 6: Produzir checklist de deploy**

Entregar ao responsável:

- origens a cadastrar no Google;
- variáveis de backend e Netlify;
- comandos de deploy na ordem correta;
- checks de `/health`, 401 sem token e login corporativo;
- identificação da revisão Cloud Run e deploy Netlify anteriores para rollback.

**Step 7: Commit somente se houve correção durante a verificação**

```bash
git add <somente-arquivos-da-correção>
git commit -m "fix(console): address production readiness verification"
```

Não criar commit vazio.

---

## Critério de conclusão da implementação

O trabalho só está concluído quando:

1. todas as rotas `/console` exigem Google SSO ou bypass local duplamente guardado;
2. o JWT interno continua protegendo viajantes e staff;
3. qualquer conta válida `@parrottrips.com` tem acesso completo, sem banco de usuários;
4. fases publicadas não são mutáveis;
5. o editor salva fase, checklist e links em uma única transação;
6. a sessão vive apenas em `sessionStorage` e resiste ao cenário de 401 concorrente;
7. CORS, docs e configuração falham de forma fechada em produção;
8. testes e builds relevantes passam com evidência recente;
9. deploy e rollback estão documentados, mas nenhum deploy ocorreu sem autorização explícita.
