# Usuário de Teste — Marcelo (Perfil Completo)

Documento de rastreamento para o usuário de teste com todos os campos populados, criado para validar a visão completa do viajante no app — perfil, dados WeTravel (pacote + add-ons), progresso de checklist e Service Agreement.

---

## Identificadores

| Campo | Valor |
|---|---|
| `user_id` | `e3dae095-7520-4afc-8b67-542e1783ff7d` |
| `phone` | `+5512991296651` |
| `email` | `angelo@parrottrips.com` |
| `full_name` | `Marcelo Angelo da Silva Filho` |
| `wetravel_trip_uuid` | `TEST-2026-FULL` |
| `order_id` | `ORDER-TEST-001` |
| `participant_id` | `TEST-MARCELO-001` |
| JWT (devUsers.ts) | entry label `Marcelo — TEST-2026-FULL` |

---

## O que foi criado

### `users` — 1 linha

Criado manualmente antes do seed de perfil.

| campo | valor |
|---|---|
| `phone` | `+5512991296651` |
| `full_name` | `Marcelo Angelo da Silva Filho` |
| `email` | `angelo@parrottrips.com` |
| `role` | `traveler` |
| `status` | `active` |

---

### `trip_travelers` — 1 vínculo

Liga o usuário à viagem `TEST-2026-FULL`.

---

### `traveler_profiles` — 1 linha (todos os campos)

Populado com dados realistas para validar cada seção do perfil no app.

| campo | valor |
|---|---|
| `preferred_name` | `Marcelo` |
| `date_of_birth` | `1990-03-15` |
| `gender` | `male` |
| `passport_first_name` | `Marcelo Angelo` |
| `passport_last_name` | `da Silva Filho` |
| `passport_country` | `Brazil` |
| `passport_number` | `AB1234567` |
| `passport_issue_date` | `2020-06-10` |
| `passport_expiration_date` | `2030-06-10` |
| `dietary_restrictions_flag` | `false` |
| `dietary_restrictions_details` | `null` |
| `seasickness_flag` | `false` |
| `plus_one_flag` | `true` |
| `plus_one_name` | `Vitor Sanches` |
| `plus_one_email` | `vitor@parrottrips.com` |
| `needs_flight_help_flag` | `false` |
| `needs_travel_insurance_help_flag` | `true` |
| `unforgettable_trip_details` | `DJ tocar Raul Seixas na praia ao pôr do sol` |
| `service_agreement_url` | `https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf` |

---

### `wetravel_participant_phones` — 1 linha

Bridge que conecta o número de telefone ao e-mail na base WeTravel, permitindo que o app encontre os dados de pagamento do viajante.

| campo | valor |
|---|---|
| `phone` | `+5512991296651` |
| `email` | `angelo@parrottrips.com` |
| `trip_uuid` | `TEST-2026-FULL` |
| `order_id` | `ORDER-TEST-001` |
| `participant_id` | `TEST-MARCELO-001` |
| `full_name` | `Marcelo Angelo da Silva Filho` |

---

### `wetravel_bookings` — 1 linha

Simula um booking confirmado WeTravel. Inclui `participants_json` para que a view `host_trip_participants` consiga identificar o e-mail do participante.

| campo | valor |
|---|---|
| `order_id` | `ORDER-TEST-001` |
| `trip_uuid` | `TEST-2026-FULL` |
| `trip_currency` | `USD` |
| `buyer_email` | `angelo@parrottrips.com` |
| `total_paid_amount` | `299900` (= $2.999,00 — armazenado em centavos) |
| `booking_event_type` | `booking_confirmed` |
| `participants_json` | `[{"id": "TEST-MARCELO-001", "full_name": "...", "email": "angelo@parrottrips.com"}]` |

---

### `wetravel_payments` — 1 linha

Simula um pagamento processado com cartão de crédito.

| campo | valor |
|---|---|
| `payment_id` | `PAY-TEST-MARCELO-001` |
| `order_id` | `ORDER-TEST-001` |
| `status` | `processed` |
| `payment_method` | `credit_card` |
| `currency` | `USD` |
| `total_amount` | `299900` |

---

### `wetravel_order_options` — 4 linhas

Simula o pacote escolhido e os add-ons contratados.

| `option_id` | `option_type` | `option_name` | `price` |
|---|---|---|---|
| `OPT-TEST-PKG-001` | `package` | `Brazil Trek Standard` | `199900` ($1.999,00) |
| `OPT-TEST-ADDON-001` | `option` | `Airport Transfer` | `15000` ($150,00) |
| `OPT-TEST-ADDON-002` | `option` | `Travel Insurance` | `35000` ($350,00) |
| `OPT-TEST-ADDON-003` | `personal_option` | `eSIM Card` | `5000` ($50,00) |

---

## Como os dados chegam ao app (pipeline WeTravel)

O app **não lê as tabelas `wetravel_*` diretamente**. Ele usa duas views:

```
wetravel_bookings ─┐
wetravel_payments  ├──► host_trip_purchases ──► host_trip_participants
wetravel_order_options ─┘                              │
wetravel_transactions ─┘                               │
                                               JOIN wetravel_participant_phones
                                                       │
                                               WHERE phone = :phone
                                               AND trip_uuid = :trip_uuid
```

**`host_trip_purchases`**: agrega `package_names`, `addon_names`, `paid_amount` e `currency` por `order_id`, unindo bookings + payments + order_options.

**`host_trip_participants`**: expande os participantes via `participants_json` do booking, expondo um `participant_email` por linha.

**`wetravel_participant_phones`**: bridge phone ↔ email ↔ trip_uuid. É a tabela que o app usa para localizar qual email na view corresponde ao número de telefone do usuário logado.

O endpoint `/me/profile` executa:

```sql
SELECT htp.package_names, htp.addon_names, htp.paid_amount, htp.currency
FROM host_trip_participants htp
JOIN wetravel_participant_phones wpp
    ON wpp.email = htp.participant_email AND wpp.trip_uuid = htp.trip_uuid
WHERE wpp.phone = :phone AND wpp.trip_uuid = :trip_uuid
LIMIT 1
```

**Importante:** `host_trip_participants` e `host_trip_purchases` são **views** — não aceita INSERT/DELETE. Toda inserção deve ser feita nas tabelas base (`wetravel_bookings`, `wetravel_payments`, `wetravel_order_options`).

---

## Como recriar (script)

```bash
cd backend
poetry run python scripts/seed_marcelo_test_user.py
```

O script:
1. Insere/atualiza as 3 tabelas WeTravel via `ON CONFLICT ... DO UPDATE`
2. Verifica a view `host_trip_participants` e imprime o resultado
3. Gera um JWT válido por 90 dias
4. Adiciona a entrada no `frontend/src/config/devUsers.ts` (se ainda não estiver lá)

Para regenerar o token depois de expirado: rodar o script novamente (o ON CONFLICT garante idempotência).

---

## Como verificar

### 1. Perfil completo via SQL

```sql
SELECT tp.preferred_name, tp.passport_first_name, tp.passport_last_name,
       tp.passport_country, tp.plus_one_name, tp.service_agreement_url
FROM traveler_profiles tp
JOIN trip_travelers tt ON tt.id = tp.trip_traveler_id
JOIN users u ON u.id = tt.user_id
WHERE u.phone = '+5512991296651';
```

### 2. Dados WeTravel (o que o app recebe)

```sql
SELECT htp.package_names, htp.addon_names, htp.paid_amount, htp.currency
FROM host_trip_participants htp
JOIN wetravel_participant_phones wpp
    ON wpp.email = htp.participant_email AND wpp.trip_uuid = htp.trip_uuid
WHERE wpp.phone = '+5512991296651' AND wpp.trip_uuid = 'TEST-2026-FULL';
```

Resultado esperado:
```
package_names    | Brazil Trek Standard
addon_names      | Airport Transfer, eSIM Card, Travel Insurance
paid_amount      | 299900
currency         | USD
```

### 3. No app

No dev switcher, selecionar `Marcelo — TEST-2026-FULL`. Verificar:

- **Perfil** → todos os campos preenchidos, incluindo passaporte, acompanhante (Vitor Sanches), preferências
- **Produtos & Pagamento** → `Brazil Trek Standard` + add-ons + valor `$2,999.00`
- **Service Agreement** → botão "View Service Agreement" visível (link para PDF de teste)

---

## Como remover

```sql
-- 1. Progresso do usuário (se tiver interagido)
DELETE FROM traveler_checklist_progress
WHERE trip_traveler_id IN (
    SELECT tt.id FROM trip_travelers tt
    JOIN users u ON u.id = tt.user_id
    WHERE u.phone = '+5512991296651'
);

DELETE FROM traveler_phase_progress
WHERE trip_traveler_id IN (
    SELECT tt.id FROM trip_travelers tt
    JOIN users u ON u.id = tt.user_id
    WHERE u.phone = '+5512991296651'
);

-- 2. Perfil
DELETE FROM traveler_profiles
WHERE trip_traveler_id IN (
    SELECT tt.id FROM trip_travelers tt
    JOIN users u ON u.id = tt.user_id
    WHERE u.phone = '+5512991296651'
);

-- 3. Bridge WeTravel
DELETE FROM wetravel_participant_phones WHERE phone = '+5512991296651';

-- 4. Dados WeTravel (tabelas base)
DELETE FROM wetravel_order_options WHERE order_id = 'ORDER-TEST-001';
DELETE FROM wetravel_payments WHERE order_id = 'ORDER-TEST-001';
DELETE FROM wetravel_bookings WHERE order_id = 'ORDER-TEST-001';

-- 5. Vínculo viajante ↔ viagem
DELETE FROM trip_travelers
WHERE user_id = (SELECT id FROM users WHERE phone = '+5512991296651');

-- 6. Usuário
DELETE FROM users WHERE phone = '+5512991296651';
```

Após o SQL, remover a entrada do `devUsers.ts` manualmente ou regenerar:

```bash
cd backend && poetry run python scripts/gen_dev_users.py
```

---

## Diferença em relação aos usuários `+1555TEST{N}`

| | Marcelo (`+5512991296651`) | Usuários `+1555TEST{N}` |
|---|---|---|
| origem | criado manualmente com `seed_marcelo_test_user.py` | gerados por `gen_dev_users.py` |
| perfil | todos os campos populados | nenhum campo populado (perfil criado pelo usuário ao interagir) |
| WeTravel | bookings + payments + order_options inseridos | nenhum dado WeTravel |
| propósito | testar a visão completa do viajante | testar cada viagem real com acesso mínimo |
| token expiry | 90 dias | 30 dias |