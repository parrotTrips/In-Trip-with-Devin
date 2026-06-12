# Staff App — Design

---

## Fluxo de acesso

```
Login (WhatsApp OTP)
  │
  ├── role = traveler  →  App do viajante (pré-trip / in-trip)
  │
  └── role = staff     →  Staff App
```

A verificação é feita pelo campo `role` na tabela `users` do Supabase. Default é `traveler`. Staff precisa ter `role = 'staff'` cadastrado manualmente.

---

## Estrutura do Staff App

Três abas na bottom navigation:

### 1. Itinerary (🗺 Roteiro)

- Lista de dias da viagem em cards colapsáveis
- Cada dia mostra o total de check-ins do dia (ex: "9/12 ✓")
- Ao expandir o dia, aparecem as atividades com:
  - Horário e título
  - Contador de viajantes presentes (ex: "9/12 travelers")
  - Ícone de status: ✅ todos presentes · ⚠️ parcial · ○ nenhum
- Ao expandir uma atividade, aparecem:
  - Descrição detalhada para o staff
  - Barra de progresso de presença
  - Botão **Scan QR** que abre o leitor de QR Code

### 2. QR Scan (📷 Leitor)

- Viewfinder de câmera para escanear o QR Code fixo do viajante
- Seletor de atividade (para qual check-in o scan está sendo feito)
- Lista de últimos scans realizados na sessão

### 3. Contacts (🎧 Contatos)

- Guias locais, hospedagem, transporte e emergências
- Cada contato tem nome, função e botão de ligar direto (`tel:`)
- Dados populados via planilha (mesmo pipeline do conteúdo da viagem)

---

## QR Code dos viajantes

- Cada viajante tem um QR Code **fixo** — não muda entre atividades
- O QR Code representa o `user_id` do viajante no Supabase
- O staff escaneia o QR do viajante para registrar presença em uma atividade específica
- O check-in é salvo em `traveler_activity_checkins` (tabela a criar): `user_id + activity_id + timestamp`

---

## Banco de dados — o que falta criar

| Tabela | Campos mínimos | Descrição |
|---|---|---|
| `trip_contacts` | `id`, `wetravel_trip_uuid`, `category`, `name`, `role`, `phone`, `sort_order` | Contatos por viagem — populados via planilha |
| `traveler_activity_checkins` | `id`, `user_id`, `trip_activity_id`, `checked_in_at`, `checked_in_by` | Registra presença de viajante em cada atividade via QR |

A coluna `role` em `users` já existe (`traveler` / `staff`) — nenhuma migration necessária para o acesso.

---

## Planilha — aba nova

Adicionar aba **Contatos** na planilha Google Sheets com as colunas:
```
trip_uuid | category | name | role | phone | sort_order
```

O pipeline de import (`import_trip_content.py`) e o `Code.gs` precisam suportar essa nova aba.

---

## Switch staff ↔ viajante

Botão no header do Staff App que permite ao staff ver o app como um viajante veria — útil para conferir o conteúdo que o viajante está recebendo. A ser implementado após o layout estar aprovado.

---

## Status atual

- ✅ Roteamento por role=staff funciona (`App.tsx`)
- ✅ Itinerary com dados reais do banco (`GET /me/staff/trip`)
- ✅ Switch staff ↔ viajante (banner laranja + botão no header)
- ⏳ Contatos: tabela no banco + aba na planilha + pipeline + endpoint
- ⏳ QR Code: câmera real + registro de check-in no banco (`traveler_activity_checkins`)
