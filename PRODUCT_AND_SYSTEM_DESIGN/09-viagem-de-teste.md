# Viagem de Teste — Mapa de Criação e Remoção

Documento de rastreamento para a viagem de teste criada para validar o fluxo completo do app com todos os campos. Tudo listado aqui foi criado intencionalmente para teste e deve ser removido com os comandos da seção "Como remover".

---

## Identificadores da viagem de teste

| Campo | Valor |
|---|---|
| `wetravel_trip_uuid` | `TEST-2026-FULL` |
| `title` | `Viagem de Teste — Full Coverage` |
| `start_date` | `2026-07-01` |
| Telefones dos usuários de teste | `+1555TEST{N}` (gerado por `gen_dev_users.py`) |

---

## O que será criado

### `wetravel_trips` — 1 linha

Inserida manualmente antes de rodar os scripts:

```sql
INSERT INTO wetravel_trips (trip_uuid, title, start_date, created_at, updated_at)
VALUES ('TEST-2026-FULL', 'Viagem de Teste — Full Coverage', '2026-07-01', now(), now());
```

---

### `users` — 1 usuário de teste

Criado pelo `gen_dev_users.py`. O phone segue o padrão `+1555TEST{N}` onde N é a posição da viagem na listagem ordenada por `start_date`. Verificar o número exato no output do script.

| Campo | Valor |
|---|---|
| `phone` | `+1555TEST{N}` (ver output do script) |
| `full_name` | `Test Traveler — Viagem de Teste — Full C` |
| `role` | `traveler` |
| `status` | `active` |

---

### `trip_travelers` — 1 vínculo

Criado pelo `gen_dev_users.py`. Liga o usuário de teste à viagem `TEST-2026-FULL`.

---

### `trip_phases` — 14 fases

Criadas pelo `seed_placeholder_trip.py`. 4 pre-trip + 10 in-trip.

| sort_order | slug | phase_type | título |
|---|---|---|---|
| 0 | visa | pre-trip | Visa |
| 1 | vaccination | pre-trip | Vaccination |
| 2 | packing | pre-trip | How to Pack |
| 3 | documents | pre-trip | Documents |
| 4 | day1 | in-trip | Day 1 — Jul 1 |
| 5 | day2 | in-trip | Day 2 — Jul 2 |
| 6 | day3 | in-trip | Day 3 — Jul 3 |
| 7 | day4 | in-trip | Day 4 — Jul 4 |
| 8 | day5 | in-trip | Day 5 — Jul 5 |
| 9 | day6 | in-trip | Day 6 — Jul 6 |
| 10 | day7 | in-trip | Day 7 — Jul 7 |
| 11 | day8 | in-trip | Day 8 — Jul 8 |
| 12 | day9 | in-trip | Day 9 — Jul 9 |
| 13 | day10 | in-trip | Day 10 — Jul 10 |

Campos cobertos: `id`, `wetravel_trip_uuid`, `phase_type`, `title`, `subtitle`, `icon`, `short_description`, `detailed_description`, `sort_order`, `starts_at` (só in-trip), `is_locked_by_default`, `is_visible`.

---

### `trip_phase_checklist_items` — 31 itens

Criados pelo `seed_placeholder_trip.py`. Distribuídos pelas 4 fases pre-trip.

| fase | qtd de itens |
|---|---|
| Visa | 5 |
| Vaccination | 5 |
| How to Pack | 12 |
| Documents | 9 |

Campos cobertos: `id`, `trip_phase_id`, `label`, `sort_order`, `is_required`.

**Campo NÃO populado pelo seed atual:** `description` (campo existe na tabela mas fica `null`). Para testar esse campo, inserir manualmente no banco após o seed.

---

### `trip_phase_links` — 8 links

Criados pelo `seed_placeholder_trip.py`. 2 links por fase pre-trip.

Campos cobertos: `id`, `trip_phase_id`, `label`, `url`, `sort_order`.

---

### `trip_activities` — 31 atividades

Criadas pelo `seed_placeholder_trip.py`. Distribuídas pelos 10 dias in-trip. Cobrem os 4 tipos: `included`, `optional`, `suggested`, `logistics`.

Campos cobertos: `id`, `trip_phase_id`, `name`, `activity_type`, `duration_minutes`, `short_description`, `sort_order`.

**Campos NÃO populados pelo seed atual:**

| campo | motivo |
|---|---|
| `practical_info` | omitido por brevidade no seed — inserir manualmente para testar |
| `amount_brl` | não populado — relevante para atividades `optional` |
| `starts_at` | o seed usa `time` como texto em `short_description`, não como timestamp |

Para testar esses campos, rodar após o seed:

```sql
-- Exemplo: adicionar practical_info e amount_brl a uma atividade optional
UPDATE trip_activities
SET
    practical_info = 'Levar protetor solar e água. Ponto de encontro: lobby do hotel às 08h50.',
    amount_brl = 150.00
WHERE
    trip_phase_id IN (SELECT id FROM trip_phases WHERE wetravel_trip_uuid = 'TEST-2026-FULL')
    AND activity_type = 'optional'
LIMIT 1;
```

---

### `activity_media` — 0 linhas (não criadas pelos scripts)

A tabela existe mas o frontend ainda não usa. Nenhuma linha criada pelos scripts.

---

### Criadas durante os testes (interação do usuário)

Estas linhas são criadas automaticamente quando o usuário de teste interage com o app:

| tabela | quando é criada |
|---|---|
| `otp_codes` | ao solicitar OTP no login (expira em 10 min, mas a linha permanece) |
| `traveler_checklist_progress` | ao marcar/desmarcar item de checklist |
| `traveler_phase_progress` | ao concluir uma fase |
| `traveler_profiles` | ao salvar o perfil pela primeira vez |

---

### `frontend/src/config/devUsers.ts`

Arquivo local gerado pelo `gen_dev_users.py`. Está no `.gitignore` — nunca foi commitado. Contém tokens JWT válidos por 30 dias. Deletar o arquivo encerra o acesso do dev switcher, sem impacto no banco.

---

## Como criar

### 1. Inserir a viagem no banco

```sql
INSERT INTO wetravel_trips (trip_uuid, title, start_date, created_at, updated_at)
VALUES ('TEST-2026-FULL', 'Viagem de Teste — Full Coverage', '2026-07-01', now(), now());
```

### 2. Popular fases e atividades

```bash
cd backend
env/bin/python3 scripts/seed_placeholder_trip.py \
  --trip-uuid TEST-2026-FULL \
  --start-date 2026-07-01
```

### 3. Criar usuário de teste e gerar devUsers.ts

```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

### 4. (Opcional) Popular campos não cobertos pelo seed

Ver os UPDATE de exemplo na seção `trip_activities` acima.

---

## Como remover tudo

Executar na ordem abaixo para respeitar as foreign keys.

```sql
-- 1. Progresso do usuário de teste
DELETE FROM traveler_checklist_progress
WHERE trip_traveler_id IN (
    SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

DELETE FROM traveler_phase_progress
WHERE trip_traveler_id IN (
    SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

-- 2. Perfil do usuário de teste
DELETE FROM traveler_profiles
WHERE trip_traveler_id IN (
    SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

-- 3. Conteúdo das fases
DELETE FROM trip_activities
WHERE trip_phase_id IN (
    SELECT id FROM trip_phases WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

DELETE FROM trip_phase_checklist_items
WHERE trip_phase_id IN (
    SELECT id FROM trip_phases WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

DELETE FROM trip_phase_links
WHERE trip_phase_id IN (
    SELECT id FROM trip_phases WHERE wetravel_trip_uuid = 'TEST-2026-FULL'
);

-- 4. Fases
DELETE FROM trip_phases WHERE wetravel_trip_uuid = 'TEST-2026-FULL';

-- 5. Vínculo viajante ↔ viagem
DELETE FROM trip_travelers WHERE wetravel_trip_uuid = 'TEST-2026-FULL';

-- 6. Usuário de teste
-- Atenção: só remover se o telefone for exclusivo desta viagem de teste
-- Verificar o phone exato no output do gen_dev_users.py antes de executar
DELETE FROM users WHERE phone LIKE '+1555TEST%'
  AND full_name LIKE 'Test Traveler — Viagem de Teste%';

-- 7. OTP codes do usuário de teste (opcional — expiram sozinhos)
DELETE FROM otp_codes WHERE phone LIKE '+1555TEST%';

-- 8. A viagem em si
DELETE FROM wetravel_trips WHERE trip_uuid = 'TEST-2026-FULL';
```

Após executar o SQL, deletar o arquivo local:

```bash
rm frontend/src/config/devUsers.ts
```

E regenerar o `devUsers.ts` sem a viagem de teste:

```bash
cd backend && env/bin/python3 scripts/gen_dev_users.py
```

---

## Campos ainda sem cobertura no app

Campos que existem no banco mas o frontend ainda não lê/exibe — não precisam ser testados agora, mas estão documentados aqui para referência:

| tabela | campo | status |
|---|---|---|
| `trip_activities` | `practical_info` | backend retorna, frontend não exibe ainda |
| `trip_activities` | `amount_brl` | backend retorna, frontend não exibe ainda |
| `trip_activities` | `starts_at` (timestamp) | seed usa texto em short_description em vez de timestamp |
| `trip_phase_checklist_items` | `description` | campo existe, não populado pelo seed |
| `activity_media` | toda a tabela | tabela existe, frontend não usa ainda |
