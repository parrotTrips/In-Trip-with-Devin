# Parrot Trips - App de Experiencia Durante a Viagem

Aplicativo web da Parrot Trips para acompanhar uma viagem em grupo no Brasil. Ele combina autenticacao por WhatsApp, mapa de progresso da viagem, checklists por fase, comentarios colaborativos, notificacoes, perfil do viajante e missoes gamificadas.

Este repositorio tem dois blocos principais:

- `frontend/`: interface do app em React + Vite
- `backend/`: API em FastAPI com persistencia em SQLite

## Visao Geral

O app foi pensado para funcionar como um companion app da viagem. Em vez de ser apenas um painel administrativo, ele acompanha o viajante ao longo da experiencia.

Na pratica, a pessoa entra no app, se autentica, visualiza onde esta na jornada, abre detalhes de cada fase, marca itens como concluidos, comenta em fases e dias da viagem, consulta notificacoes e participa de desafios e missoes.

Boa parte da experiencia gira em torno de uma linha do tempo visual da trip. O backend guarda o estado dinamico de cada viajante, enquanto o frontend monta a navegacao e a apresentacao dessas informacoes.

## Demo

- Frontend: `https://parrottrips-app-ke2ylzmt.devinapps.com`
- Backend API: `https://app-rxxkezkz.fly.dev`
- Docs da API: `https://app-rxxkezkz.fly.dev/docs`

## O Que o App Faz

- login por numero de telefone com OTP via WhatsApp
- mapa principal da viagem com fases pre-trip e in-trip
- tela de detalhes de fase com checklist e comentarios
- tela de detalhes de dia com roteiro, atividades e album
- perfil do viajante com dados da experiencia
- notificacoes e avisos
- missoes e leaderboard
- documentos, recomendacoes, contatos de emergencia e compartilhamento

## Como Rodar Localmente

### Pre-requisitos

- Node.js 18 ou superior
- Python 3.12 ou superior
- Poetry instalado

### 1. Subir o backend

```bash
cd backend
poetry install
cp .env.example .env
poetry run fastapi dev app/main.py
```

Backend local padrao: `http://localhost:8000`

### 2. Configurar o frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Se quiser usar o backend local, ajuste `frontend/.env` para:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Subir o frontend

```bash
cd frontend
npm run dev
```

Frontend local padrao: `http://localhost:5173`

## Como Testar a Aplicacao

Existem dois jeitos principais de testar o app localmente.

### Fluxo real com OTP

Esse modo reproduz melhor o comportamento real do produto.

1. suba o backend
2. suba o frontend
3. abra o app no navegador
4. informe um telefone valido
5. solicite o codigo OTP
6. valide o codigo para entrar no app

Esse caminho depende do backend e, se voce quiser entrega real por WhatsApp, tambem depende das credenciais da Meta configuradas no `.env` do backend.

### Fluxo rapido para desenvolvimento, sem OTP

Se a sua meta for apenas navegar no app como se fosse um viajante, existe um bypass de login disponivel somente em desenvolvimento.

Rode o frontend assim:

```bash
cd frontend
VITE_DEV_AUTO_LOGIN=true npm run dev
```

Com isso, o app entra direto em uma sessao autenticada quando nao existir `parrot_user` salvo no navegador.

Voce tambem pode definir um usuario fake especifico:

```bash
cd frontend
VITE_DEV_AUTO_LOGIN=true \
VITE_DEV_USER_ID=7 \
VITE_DEV_USER_PHONE=+5511999999999 \
VITE_DEV_USER_NAME="Viajante Teste" \
npm run dev
```

Esse atalho:

- so funciona em ambiente de desenvolvimento
- nao muda o comportamento de producao
- nao substitui uma sessao real ja salva no `localStorage`

Se quiser voltar ao fluxo normal de login, basta parar de usar a flag `VITE_DEV_AUTO_LOGIN` e recarregar o app.

## Variaveis de Ambiente

### Frontend

Arquivo: `frontend/.env`

| Variavel | Para que serve | Exemplo |
|---|---|---|
| `VITE_API_URL` | URL da API usada pelo frontend | `http://localhost:8000` |
| `VITE_DEV_AUTO_LOGIN` | ativa o auto-login em desenvolvimento | `true` |
| `VITE_DEV_USER_ID` | id do usuario fake de dev | `7` |
| `VITE_DEV_USER_PHONE` | telefone do usuario fake de dev | `+5511999999999` |
| `VITE_DEV_USER_NAME` | nome exibido do usuario fake de dev | `Viajante Teste` |

### Backend

Arquivo: `backend/.env`

| Variavel | Para que serve |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | identificador do numero na Meta |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | identificador da conta WhatsApp Business |
| `WHATSAPP_ACCESS_TOKEN` | token de acesso da API da Meta |
| `WHATSAPP_TEMPLATE_NAME` | nome do template de autenticacao |
| `DATABASE_PATH` | caminho do arquivo SQLite |

## Fluxo Em Alto Nivel de Como o Sistema Funciona

### 1. Entrada no app

O frontend inicia a aplicacao e decide se o usuario esta logado ou nao.

- se existir uma sessao salva, ele entra direto no app
- se estiver em desenvolvimento com auto-login ligado, ele cria uma sessao fake
- se nao houver sessao, ele mostra a tela de login

### 2. Login

No fluxo normal, a pessoa informa o telefone e pede um codigo OTP.

O frontend envia esse telefone para o backend. O backend gera o codigo, guarda no banco e tenta enviar via WhatsApp. Depois disso, o usuario informa o codigo recebido e o backend valida a autenticacao. Quando a validacao passa, o frontend salva a sessao localmente e o app passa a funcionar como usuario autenticado.

### 3. Navegacao principal

Depois de logado, o usuario cai no mapa principal da viagem.

Essa tela funciona como a visao central da experiencia. Ela mostra:

- as fases da viagem
- onde o viajante esta
- o ritmo ideal sugerido pelo mascote
- o caminho entre momentos pre-trip e in-trip

Desse mapa saem os acessos para os detalhes de cada fase e para os dias da viagem.

### 4. Fases e dias

As telas de fase e de dia sao o coracao da experiencia operacional.

Nas fases, o viajante encontra instrucoes, checklist, progresso e comentarios.

Nos dias da viagem, ele encontra a agenda, atividades, informacoes praticas, comentarios e elementos visuais da experiencia daquele momento.

Essas telas misturam duas fontes:

- conteudo da trip, que hoje ainda esta em boa parte organizado no frontend
- estado dinamico do usuario, que vem do backend

### 5. Estado do viajante

O backend guarda o que muda de pessoa para pessoa. Por exemplo:

- progresso de checklist
- conclusao de fases
- comentarios
- perfil
- notificacoes
- progresso nas missoes

Isso permite que a experiencia nao seja apenas estatica. Dois viajantes podem olhar a mesma viagem, mas com estados diferentes.

### 6. Missoes, notificacoes e perfil

Fora do mapa principal, o app tem areas de apoio importantes:

- missoes: camada de engajamento e pontuacao
- notificacoes: comunicacao operacional e avisos
- perfil: dados do viajante e informacoes complementares da experiencia

Essas partes ajudam a transformar o app em uma ferramenta de acompanhamento continuo, e nao apenas uma tela de consulta.

## Estrutura Principal do Repositorio

### Frontend

O frontend esta organizado para separar composicao global, features e elementos compartilhados.

```text
frontend/src/
  app/        ponto de entrada da aplicacao, router e providers
  features/   telas e servicos agrupados por dominio
  shared/     componentes e cliente base de API
  test/       setup de testes e mocks
```

Em alto nivel:

- `app/` cuida da entrada da aplicacao e da autenticacao local
- `features/` concentra as telas e chamadas de API por area do produto
- `shared/` guarda o que e reutilizado entre varias partes do app

### Backend

O backend esta modularizado por responsabilidade.

```text
backend/app/
  core/      configuracoes gerais
  db/        acesso e inicializacao do banco
  routers/   endpoints HTTP
  schemas/   modelos de dados
  services/  regras de negocio
```

Em alto nivel:

- `routers/` recebem as requisicoes
- `services/` executam a logica principal
- `schemas/` definem os formatos de entrada e saida
- `db/` cuida da persistencia

## Comandos Uteis

### Frontend

```bash
cd frontend
npm run dev
npm run test -- --run
npm run lint
npm run build
```

### Backend

```bash
cd backend
poetry install
poetry run fastapi dev app/main.py
```

## Endpoints Principais da API

| Metodo | Endpoint | Uso principal |
|---|---|---|
| `GET` | `/healthz` | health check |
| `POST` | `/auth/request-otp` | solicitar OTP |
| `POST` | `/auth/verify-otp` | validar OTP e entrar |
| `GET` | `/users/{user_id}` | consultar usuario |
| `PUT` | `/users/{user_id}` | atualizar usuario |
| `GET` | `/profile/{user_id}` | consultar perfil |
| `PUT` | `/profile/{user_id}` | atualizar perfil |
| `POST` | `/checklist/update` | atualizar checklist |
| `GET` | `/checklist/{trip_id}/{user_id}` | ler progresso do checklist |
| `POST` | `/phases/complete` | marcar fase como concluida |
| `GET` | `/phases/{trip_id}/{user_id}` | ler fases concluidas |
| `GET` | `/missions/{trip_id}` | listar missoes |

## Viagem Atual no Projeto

O conteudo atual do app representa uma experiencia de viagem da Parrot Trips no Brasil, com foco em Rio de Janeiro e Ilha Grande.

Mesmo quando a camada visual da trip esta no frontend, o backend ainda e responsavel por guardar o estado que muda durante o uso real da aplicacao.

## Resumo Final

Se voce quer testar rapido:

1. suba o backend em `localhost:8000`
2. aponte o frontend para esse backend
3. rode o frontend com `VITE_DEV_AUTO_LOGIN=true`
4. abra `http://localhost:5173`

Se voce quer validar o fluxo real:

1. rode backend e frontend
2. entre pelo login
3. solicite o OTP
4. autentique e navegue pelo mapa, fases, dias, perfil, notificacoes e missoes
