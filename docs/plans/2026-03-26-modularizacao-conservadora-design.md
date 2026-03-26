# Design: Modularizacao Conservadora com Testes e Documentacao

## Contexto

O projeto possui um frontend React/Vite e um backend FastAPI/SQLite. A base atual funciona, mas concentra responsabilidades demais em poucos arquivos:

- o backend esta quase todo em `backend/app/main.py`;
- o frontend possui separacao inicial por `pages`, `components`, `services` e `data`, mas sem modulos por dominio;
- nao ha estrutura de testes configurada no frontend;
- o backend praticamente nao possui testes automatizados.

O objetivo desta refatoracao e melhorar a organizacao interna sem alterar o comportamento publico do sistema.

## Objetivos

- modularizar o backend por responsabilidade e dominio, mantendo os mesmos endpoints;
- modularizar o frontend por dominio, mantendo as mesmas telas e rotas;
- documentar funcoes e modulos para facilitar manutencao;
- introduzir testes unitarios e de integracao para backend e frontend;
- preservar o comportamento atual durante todo o processo.

## Nao objetivos

- mudar regras de negocio;
- redesenhar a UI;
- alterar contratos HTTP existentes;
- migrar SQLite para outro banco;
- transformar o conteudo estatico da trip em conteudo backend-driven.

## Abordagem escolhida

Foi aprovada uma modularizacao conservadora estruturada.

### Backend

O backend sera reorganizado para:

```text
backend/app/
  main.py
  core/
    config.py
  db/
    database.py
  schemas/
    auth.py
    users.py
    profile.py
    checklist.py
    comments.py
    notifications.py
    missions.py
  services/
    auth_service.py
    user_service.py
    profile_service.py
    checklist_service.py
    comment_service.py
    notification_service.py
    mission_service.py
  routers/
    health.py
    auth.py
    users.py
    profile.py
    checklist.py
    comments.py
    notifications.py
    missions.py
```

#### Responsabilidades

- `main.py`: compoe a aplicacao FastAPI, registra middleware e inclui routers;
- `core/config.py`: centraliza leitura de variaveis de ambiente e constantes globais;
- `db/database.py`: inicializacao do banco e helpers de conexao;
- `schemas/`: concentra os modelos Pydantic por dominio;
- `services/`: concentra regras de negocio e acesso a dados;
- `routers/`: define os endpoints e delega o trabalho aos services.

### Frontend

O frontend sera reorganizado para:

```text
frontend/src/
  app/
    App.tsx
    router.tsx
    providers/
      AuthProvider.tsx
  features/
    auth/
      pages/LoginScreen.tsx
      services/auth-api.ts
    trip/
      pages/HomeScreen.tsx
      pages/PhaseDetails.tsx
      pages/DayDetails.tsx
      data/tripData.ts
    profile/
      pages/ProfileScreen.tsx
      services/profile-api.ts
    missions/
      pages/MissionsScreen.tsx
      services/missions-api.ts
    notifications/
      pages/NotificationsScreen.tsx
      services/notifications-api.ts
    documents/
      pages/DocumentsScreen.tsx
    recommendations/
      pages/RecommendationsScreen.tsx
    emergency/
      pages/EmergencyContacts.tsx
    sharing/
      pages/SharingXPScreen.tsx
  shared/
    components/
      BottomNav.tsx
      TopBar.tsx
      ParrotMascot.tsx
      ProgressBar.tsx
    api/
      client.ts
    lib/
      utils.ts
    types/
```

#### Responsabilidades

- `app/`: composicao global da aplicacao, providers e roteamento;
- `features/`: funcionalidades agrupadas por dominio;
- `shared/components`: componentes reutilizaveis transversais;
- `shared/api/client.ts`: cliente HTTP base;
- `shared/lib`: utilitarios compartilhados.

## Estrategia de documentacao

### Backend

Toda funcao publica e toda funcao de service deve possuir docstring curta e objetiva, descrevendo:

- o que a funcao faz;
- entradas relevantes, se nao forem obvias;
- retorno ou efeito colateral principal, se relevante.

### Frontend

No frontend a documentacao sera leve e intencional:

- nomes de funcoes e modulos devem ser autoexplicativos;
- comentarios curtos serao adicionados apenas quando houver logica menos obvia;
- servicos de API e helpers terao comentarios sucintos quando necessario;
- arquivos novos terao organizacao clara por responsabilidade.

## Estrategia de testes

### Backend unitario

Os services serao testados isoladamente com banco SQLite temporario quando necessario. O foco sera validar regras de negocio sem depender do ciclo HTTP completo.

Cobertura inicial alvo:

- autenticacao por OTP;
- obtencao e atualizacao de usuario;
- obtencao e atualizacao de perfil;
- checklist;
- conclusao de fases;
- comentarios;
- notificacoes;
- missoes e leaderboard.

Ferramentas:

- `pytest`;
- `pytest-asyncio`;
- fixtures para banco temporario.

### Backend integracao

Os endpoints FastAPI serao testados ponta a ponta usando app de teste e banco temporario.

Cobertura inicial alvo:

- `POST /auth/request-otp`;
- `POST /auth/verify-otp`;
- `GET/PUT /users/{user_id}`;
- `GET/PUT /profile/{user_id}`;
- `POST/GET checklist`;
- `POST/GET phases`;
- `POST/GET comments`;
- notificacoes;
- missoes.

### Frontend unitario e integracao

O frontend recebera framework de testes com `Vitest` e `Testing Library`.

Cobertura inicial alvo:

- `AuthProvider`;
- tela de login;
- roteamento principal;
- `PhaseDetails`;
- `DayDetails`;
- `ProfileScreen`;
- `MissionsScreen`;
- `NotificationsScreen`.

Ferramentas:

- `vitest`;
- `jsdom`;
- `@testing-library/react`;
- `@testing-library/user-event`;
- `msw` para mock de API.

## Sequenciamento da refatoracao

Para manter risco baixo, a implementacao deve seguir esta ordem:

1. modularizar backend sem mudar contrato externo;
2. adicionar testes backend;
3. modularizar frontend sem mudar comportamento;
4. adicionar testes frontend;
5. executar verificacoes finais de build, lint e testes.

## Tratamento de risco

Os principais riscos sao:

- quebrar imports durante a reorganizacao;
- alterar sem querer contratos de endpoint;
- introduzir regressao em rotas do frontend;
- misturar refatoracao estrutural com mudancas de comportamento.

Mitigacoes:

- refatoracao incremental;
- testes criados por dominio;
- verificacao frequente de build e testes;
- nenhuma alteracao de regra de negocio durante a modularizacao.

## Resultado esperado

Ao final, o projeto deve manter a mesma experiencia funcional, mas com:

- melhor separacao de responsabilidades;
- base de testes cobrindo os fluxos principais;
- documentacao mais clara nas funcoes e modulos;
- estrutura preparada para manutencao e evolucao futura.
