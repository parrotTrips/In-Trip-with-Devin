# Autenticação, Endpoints e População de Dados

> Estado atual do sistema — maio 2026

---

## 1. Autenticação

### Visão geral

O app usa **OTP via WhatsApp + JWT**. Não há senha. O viajante recebe um código de 6 dígitos no WhatsApp, digita no app e recebe um token JWT que autentica todas as requisições seguintes.

### Fluxo passo a passo

```
Usuário digita telefone
        ↓
POST /auth/request-otp
  → verifica se o telefone existe em users
  → gera código de 6 dígitos (10 min de validade)
  → salva em otp_codes
  → envia via WhatsApp Cloud API
        ↓
Usuário recebe o código no WhatsApp e digita no app
        ↓
POST /auth/verify-otp
  → valida código em otp_codes (não usado, não expirado)
  → marca otp como usado
  → cria usuário em users se for o primeiro login
  → gera JWT com: sub (user_id), phone, role, exp
  → retorna: user_id, phone, name, role, access_token
        ↓
Frontend salva em localStorage (chave: parrot_user)
Token é incluído como Bearer em todas as requisições
```

### JWT

| Campo     | Valor                        |
|-----------|------------------------------|
| Algoritmo | HS256                        |
| Validade  | 14 dias (produção)           |
| Payload   | `sub`, `phone`, `role`, `exp` |
| Segredo   | variável de ambiente `JWT_SECRET` |

### Roles

| Role       | Quem usa                                     |
|------------|----------------------------------------------|
| `traveler` | Viajantes cadastrados em `trip_travelers`     |
| `staff`    | Equipe Parrot Trips — cadastrado manualmente via `role` na tabela `users` |

### Middleware de autenticação

Todo endpoint (exceto `/healthz` e `/auth/*`) passa pelo `JWTAuthMiddleware`. Ele:
1. Verifica o header `Authorization: Bearer <token>`
2. Decodifica o JWT e valida assinatura e expiração
3. Injeta `request.state.user_id` e `request.state.phone` para uso nos endpoints
4. Retorna 401 se o token estiver ausente, inválido ou expirado
5. Deixa requisições `OPTIONS` passarem sem validação (necessário para CORS preflight)

### CORS

Configurado para aceitar qualquer origem (`allow_origins=["*"]`). Em produção, restringir ao domínio do app.

---

## 2. Endpoints

### Autenticação — `/auth/*` (público)

| Método | Rota                  | O que faz                                         |
|--------|-----------------------|---------------------------------------------------|
| POST   | `/auth/request-otp`   | Gera e envia OTP via WhatsApp para o telefone     |
| POST   | `/auth/verify-otp`    | Valida OTP, cria usuário se necessário, retorna JWT |

**POST /auth/request-otp**
```json
// Request
{ "phone": "+5511999999999" }

// Response (WhatsApp OK)
{ "message": "OTP sent successfully" }

// Response (WhatsApp falhou — só em dev)
{ "message": "OTP generated (WhatsApp delivery failed, showing code for testing)", "debug_code": "123456" }
```

**POST /auth/verify-otp**
```json
// Request
{ "phone": "+5511999999999", "code": "123456" }

// Response
{
  "user_id": "uuid",
  "phone": "+5511999999999",
  "name": "Nome do usuário ou null",
  "role": "traveler",
  "message": "Login successful",
  "access_token": "eyJ..."
}
```

---

### Viagem — `/me/trip/*` (requer JWT)

Todos os endpoints abaixo retornam dados relativos ao usuário autenticado (identificado pelo `user_id` extraído do JWT).

| Método | Rota                          | O que faz                                              |
|--------|-------------------------------|--------------------------------------------------------|
| GET    | `/me/trip`                    | Dados gerais da viagem ativa do usuário                |
| GET    | `/me/trip/phases`             | Todas as fases visíveis da viagem                      |
| GET    | `/me/trip/phases/{phase_id}`  | Detalhe de uma fase: checklist, links e atividades     |
| GET    | `/me/trip/travelers`          | Todos os viajantes do mesmo trip com fase atual de cada um |

**GET /me/trip**
```json
{
  "trip": {
    "wetravel_trip_uuid": "6608858457",
    "title": "Wharton Brazil Trek December 2",
    "destination": "Rio de Janeiro, Brasil",
    "start_date": "2026-12-08",
    "end_date": "2026-12-17",
    "url": "https://..."
  }
}
// Retorna {"trip": null} se o usuário não tiver viagem
```

**GET /me/trip/phases**
```json
{
  "wetravel_trip_uuid": "6608858457",
  "phases": [
    {
      "id": "uuid",
      "phase_type": "pre-trip",  // ou "in-trip"
      "title": "Visa",
      "subtitle": "Entry Requirements",
      "icon": "passport",
      "short_description": "...",
      "detailed_description": "...",
      "sort_order": 0,
      "starts_at": null,         // null para pre-trip; timestamp para in-trip
      "is_locked_by_default": false,
      "checklist_items": [...],
      "links": [...]
    }
  ]
}
```

**GET /me/trip/travelers**
```json
{
  "travelers": [
    {
      "id": "uuid",
      "name": "Yujin Jung",
      "phone": "+12676894041",
      "current_phase_id": "uuid"  // fase atual estimada pelo progresso
    }
  ]
}
```

---

### Checklist e progresso — (requer JWT)

| Método | Rota                              | O que faz                                      |
|--------|-----------------------------------|------------------------------------------------|
| POST   | `/checklist/update?user_id=`      | Marca/desmarca um item de checklist            |
| GET    | `/checklist/{trip_id}/{user_id}`  | Retorna progresso do checklist por fase        |
| POST   | `/phases/complete?user_id=`       | Marca/desmarca uma fase como concluída         |
| GET    | `/phases/{trip_id}/{user_id}`     | Retorna quais fases estão concluídas           |

---

### Perfil — (requer JWT)

| Método | Rota                          | O que faz                                         |
|--------|-------------------------------|---------------------------------------------------|
| GET    | `/profile/{user_id}`          | Retorna o perfil salvo do viajante                |
| PUT    | `/profile/{user_id}`          | Cria ou atualiza o perfil do viajante             |
| GET    | `/trip/{trip_id}/travelers`   | Lista viajantes do trip (usado na seleção de quarto) |

---

### Infraestrutura

| Método | Rota       | O que faz          |
|--------|------------|--------------------|
| GET    | `/healthz` | Health check (público) |

---

## 3. Banco de dados

### Conexão

PostgreSQL hospedado no **Supabase**. A URL de conexão fica em `.env` como `DATABASE_URL`. O backend usa SQLAlchemy async (asyncpg).

Migrations gerenciadas com **Alembic**:
```
backend/alembic/versions/
  20260407_0001_initial_schema.py        ← schema original completo
  20260520_0002_add_role_and_staff_tables.py ← coluna role + tabelas staff
  20260521_0003_use_wetravel_trip_uuid.py    ← substitui trip_id por wetravel_trip_uuid
```

### Tabelas principais

| Tabela                        | Descrição                                                    |
|-------------------------------|--------------------------------------------------------------|
| `users`                       | Usuários do sistema (viajantes e staff)                      |
| `otp_codes`                   | Códigos OTP gerados, com validade e flag de uso              |
| `wetravel_trips`              | Viagens cadastradas (importadas do WeTravel)                 |
| `trip_travelers`              | Vínculo viajante ↔ viagem (N:N)                             |
| `trip_phases`                 | Fases de uma viagem (pre-trip ou in-trip)                    |
| `trip_phase_checklist_items`  | Itens do checklist de cada fase                              |
| `trip_phase_links`            | Links úteis de cada fase                                     |
| `trip_activities`             | Atividades de um dia (fases in-trip)                         |
| `traveler_checklist_progress` | Progresso de checklist por viajante                          |
| `traveler_phase_progress`     | Progresso de fase por viajante (fase concluída ou não)       |
| `trip_staff`                  | Vínculo staff ↔ viagem                                       |
| `staff_tasks`                 | Tarefas da equipe por fase (uso futuro)                      |

### Chave de identificação das viagens

As viagens são identificadas pelo `wetravel_trip_uuid` — o ID numérico da viagem no WeTravel (ex: `"6608858457"`). Esse ID aparece na URL da viagem no WeTravel e é usado como chave nas tabelas `trip_travelers`, `trip_phases`, etc.

---

## 4. Populando dados no banco

### Viajantes reais

Os viajantes reais são cadastrados manualmente em `users` com o telefone exato que usam no WhatsApp. Quando fazem o primeiro login, o sistema cria o registro automaticamente em `users` — **mas apenas se o telefone já existir na tabela** (a verificação em `request_otp` bloqueia telefones não cadastrados com 403).

O vínculo viajante ↔ viagem (`trip_travelers`) também é criado manualmente ou via script.

### Fases e atividades de uma viagem

O script `backend/scripts/seed_placeholder_trip.py` popula as fases e atividades de uma viagem específica com dados de exemplo:

```bash
cd backend
env/bin/python3 scripts/seed_placeholder_trip.py \
  --trip-uuid 6608858457 \
  --start-date 2026-12-08
```

Isso cria fases pre-trip (Visa, Vacinas, Mala, Documentos) e fases in-trip (um por dia), com checklist e atividades de exemplo.

### Usuários de teste para desenvolvimento

O script `backend/scripts/gen_dev_users.py` gera um usuário de teste por viagem cadastrada no banco:

```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

O que ele faz:
1. Lê todas as viagens de `wetravel_trips`
2. Para cada viagem, cria (ou reutiliza) um usuário com telefone `+1555TEST{N}`
3. Vincula esse usuário à viagem em `trip_travelers`
4. Verifica se a viagem tem fases cadastradas (`has_data`)
5. Gera um JWT de 30 dias para o usuário
6. Escreve `frontend/src/config/devUsers.ts` (arquivo gitignored)

Esse arquivo é consumido pelo componente `DevUserSwitcher` no frontend, que aparece apenas em modo dev (`import.meta.env.DEV`) e permite que o staff simule a visão de qualquer viajante de teste diretamente no app.

**Deve ser rodado novamente sempre que:**
- Uma nova viagem for adicionada em `wetravel_trips`
- Os tokens expirarem (validade de 30 dias)
- O `JWT_SECRET` for alterado
