# Deploy — Guia Operacional

Documentação de infraestrutura e procedimentos de deploy do aplicativo Parrot Trips.

---

## Arquitetura

```
GCP Project: jogo-da-vida-497700 (conta: angelo@parrottrips.com)

Backend (FastAPI)
  └── Cloud Run: parrot-trips-backend
       └── Artifact Registry: southamerica-east1-docker.pkg.dev/jogo-da-vida-497700/parrot-trips/backend

Frontend (React)
  └── Netlify: parrot-trips-app
       └── Site: https://parrot-trips-app-286.netlify.app
       └── SPA routing: redirect /* → /index.html (via netlify.toml)

Banco de dados
  └── Supabase (PostgreSQL) — externo, não muda
```

**URLs de produção:**
- Backend: `https://parrot-trips-backend-428743191336.southamerica-east1.run.app`
- Frontend: `https://parrot-trips-app-286.netlify.app`

---

## Pré-requisitos para rodar deploys

### Backend
1. `gcloud` CLI instalado e autenticado com `angelo@parrottrips.com`
2. Docker rodando localmente
3. `backend/.env.production` criado (ver seção abaixo)

### Frontend
1. `netlify-cli` instalado: `npm install -g netlify-cli`
2. Autenticado no Netlify: `netlify login`
3. `frontend/.env.production` com `VITE_API_URL` (ver seção abaixo)
4. Site `parrot-trips-app` já criado (feito uma vez — não precisa repetir)

### Verificar autenticação GCP (para backend)

```bash
gcloud auth list
# A conta ativa deve ser angelo@parrottrips.com

# Se precisar reautenticar:
gcloud auth login angelo@parrottrips.com
gcloud auth configure-docker southamerica-east1-docker.pkg.dev --account=angelo@parrottrips.com
gcloud config set project jogo-da-vida-497700
```

---

## Arquivos de configuração de produção

### `backend/.env.production`

Não está no git (gitignored). Criar a partir do `backend/.env.production.example`:

```bash
cp backend/.env.production.example backend/.env.production
# Editar com os valores reais
```

Formato: uma variável por linha, sem aspas, sem comentários (requerido pelo `--set-env-vars` do Cloud Run):

```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
JWT_SECRET=secret-longo-e-aleatorio
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_TEMPLATE_NAME=intripauth
WHATSAPP_TEMPLATE_LANGUAGE=en
SUPABASE_ANON_KEY=...
TRIP_CONTENT_SHEET_ID=...
```

> Os valores reais estão em `backend/.env` — basta copiar sem os comentários e sem a linha `GCP_SERVICE_ACCOUNT_JSON` (não se aplica no Cloud Run).

### `frontend/.env.production`

Não está no git (gitignored). Criar a partir do `frontend/.env.production.example`:

```bash
# Pegar a URL do backend:
make backend-url

# Criar o arquivo:
echo "VITE_API_URL=https://parrot-trips-backend-XXXXXXXX-rj.a.run.app" > frontend/.env.production
```

---

## Comandos de deploy

Todos os comandos rodam da **raiz do repositório**:

```bash
# Deploy completo (backend + frontend):
make deploy

# Só o backend:
make deploy-backend

# Só o frontend:
make deploy-frontend

# Ver logs em tempo real:
make logs

# Imprimir a URL do backend:
make backend-url

# Abrir as URLs no browser:
make open
```

### Sobrescrever a tag da imagem

Por padrão a tag é o hash curto do commit atual. Para usar uma tag customizada:

```bash
make deploy-backend IMAGE_TAG=v1.2.3
```

---

## O que acontece em cada deploy

### `make deploy-backend`

1. **`docker-build`** — Constrói a imagem `linux/amd64` do backend com a tag do commit atual e envia para o Artifact Registry (`southamerica-east1-docker.pkg.dev/jogo-da-vida-497700/parrot-trips/backend:<tag>`)
2. **`docker-push`** — Faz push da imagem para o Artifact Registry
3. **`cloud-run-deploy`** — Faz deploy no Cloud Run com as variáveis de `backend/.env.production`, imprime a URL ao final

### `make deploy-frontend`

1. **`frontend-build`** — Roda `npm run build` na pasta `frontend/` usando o `VITE_API_URL` de `frontend/.env.production`
2. **`netlify-deploy`** — Faz deploy do `dist/` para o Netlify via CLI (`netlify deploy --prod`)

O `netlify.toml` na pasta `frontend/` configura o redirect `/* → /index.html` que permite recarregar qualquer rota sem erro 404.

---

## Serviços utilizados

| Serviço | Para quê | Como acessar |
|---|---|---|
| GCP Cloud Run | Roda o backend FastAPI | Console GCP → Cloud Run → parrot-trips-backend |
| GCP Artifact Registry | Armazena imagens Docker | `southamerica-east1-docker.pkg.dev/jogo-da-vida-497700/parrot-trips/` |
| Netlify | Serve o frontend React (SPA) | app.netlify.com → parrot-trips-app |

---

## Fluxo de deploy para correções (ciclo rápido)

Durante a fase de testes com frequentes correções:

```bash
# 1. Fazer a correção no código
# 2. Commitar
git add . && git commit -m "fix: descrição da correção"

# 3. Deploy (a tag da imagem usa o hash do novo commit automaticamente)
make deploy-backend   # se foi mudança no backend
make deploy-frontend  # se foi mudança no frontend
make deploy           # se mudou os dois
```

O Cloud Run faz o rollout automaticamente sem downtime — o tráfego só é migrado para a nova revisão após o health check passar.

---

## Verificar saúde do sistema

```bash
# Backend respondendo?
curl https://parrot-trips-backend-428743191336.southamerica-east1.run.app/health

# Frontend carregando?
curl -s -o /dev/null -w "%{http_code}" https://storage.googleapis.com/parrot-trips-frontend/index.html
# Esperado: 200

# Logs do backend:
make logs
```

---

## Troubleshooting

### Token expirado (erro 403 no docker push ou gcs upload)

O token do gcloud expira com frequência. Sempre que o deploy falhar com 403 ou "Reauthentication required", rodar:

```bash
gcloud auth login angelo@parrottrips.com
gcloud auth configure-docker southamerica-east1-docker.pkg.dev --account=angelo@parrottrips.com
```

Depois repetir o comando de deploy normalmente.

### Cloud Run falhou ao criar revisão

Ver os logs de erro:

```bash
make logs
# ou direto no Console:
# Cloud Run → parrot-trips-backend → Logs
```

Causas comuns:
- Variável de ambiente faltando em `backend/.env.production`
- Erro de conexão com o Supabase (checar `DATABASE_URL`)

### Frontend carrega mas as chamadas de API falham

Verificar se `frontend/.env.production` tem a URL correta:

```bash
cat frontend/.env.production
# VITE_API_URL deve apontar para a URL do Cloud Run

# Se estiver errada, corrigir e re-deployar:
make deploy-frontend
```

### Imagem rejeitada pelo Cloud Run (manifest type error)

O Docker construiu uma imagem multi-arch. Isso não deve acontecer com o Makefile atual (`--platform linux/amd64`), mas se ocorrer:

```bash
docker build --platform linux/amd64 -t <imagem> backend/
docker push <imagem>
make cloud-run-deploy
```

---

## Estrutura de arquivos de infra no repositório

```
/
├── Makefile                          # Comandos de deploy raiz
├── backend/
│   ├── Dockerfile                    # Imagem de produção do backend
│   ├── .dockerignore                 # Exclui secrets e env do contexto Docker
│   ├── .env.production.example       # Template das variáveis de produção
│   └── .env.production               # NÃO está no git — criar localmente
└── frontend/
    ├── .env.production.example       # Template do VITE_API_URL
    └── .env.production               # NÃO está no git — criar localmente
```

---

## Histórico de decisões

| Decisão | Motivo |
|---|---|
| Cloud Run para backend | Escala a zero, cobra por request — ideal para fase de testes com baixo tráfego |
| Artifact Registry para imagens | Mesmo projeto GCP, latência baixa para o Cloud Run na mesma região |
| Cloud Storage para frontend | Firebase Hosting não pôde ser habilitado (permissão insuficiente no projeto GCP); Cloud Storage funciona igualmente bem para arquivos estáticos |
| `southamerica-east1` (São Paulo) | Região mais próxima dos usuários brasileiros |
| `--platform linux/amd64` no Docker | Cloud Run exige imagens amd64; Macs com Apple Silicon constroem arm64 por padrão |
| `--set-env-vars` com delimitador `\|` | `--env-vars-file` do Cloud Run exige YAML; o formato KEY=VALUE do `.env` não é compatível |
