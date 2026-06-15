# Fluxo de Staffs — Cadastro e Operação

---

## Visão geral

| Quem | Como entra no sistema |
|---|---|
| **Viajante** | WeTravel → webhook → Supabase (automático) |
| **Staff** | Planilha de Staff → Import → Supabase (manual, centralizado) |

---

## Planilhas

| Planilha | Para quê |
|---|---|
| **Parrot Trips — Conteúdo de Viagens** | Conteúdo das viagens (fases, checklist, roteiro). Usada pelo time de produto. |
| **Parrot Trips — Staff** | Cadastro de staffs e contatos operacionais por viagem. Usada pelo time de operações. |

---

## Planilha de Staff — abas

### Aba Viagens
Populada automaticamente pelo botão **🔄 Sync Trips**. Serve de referência para copiar `trip_uuid` nas outras abas.

### Aba Staff
Uma linha por membro de staff por viagem.

| Coluna | Descrição |
|---|---|
| `phone` | Número com código do país — ex: `+5511999999999` |
| `nome` | Nome completo do staff |
| `funcao` | Função na viagem — ex: "Lead Guide", "Support Guide" |
| `trip_uuid` | UUID da viagem (copiar da aba Viagens) |

**O que acontece ao rodar "Import Staff → Supabase":**
- Se o número **não existe** no banco → cria o usuário com `role=staff`
- Se o número **já existe** → atualiza nome e define `role=staff`
- Em todos os casos → vincula o staff à viagem em `trip_travelers`

O staff consegue fazer login via WhatsApp OTP no app e cai diretamente na visão de staff.

### Aba Contatos
Contatos operacionais da viagem (guias locais, hotéis, transporte, emergências). **Não são usuários do sistema** — são apenas uma lista de telefones visível para o staff no app.

| Coluna | Descrição |
|---|---|
| `trip_uuid` | UUID da viagem |
| `category` | Agrupamento — ex: "Local guides", "Accommodation", "Transport", "Emergency" |
| `name` | Nome do contato |
| `role` | Função — ex: "Lead guide", "Front desk" |
| `phone` | Número de contato |
| `sort_order` | Ordem dentro da categoria (1, 2, 3...) |

---

## Menu da planilha de Staff (CodeStaff.gs)

| Botão | O que faz |
|---|---|
| **🔄 Sync Trips** | Puxa as viagens ativas do Supabase para a aba Viagens |
| **Import Staff → Supabase** | Lê a aba Staff e cria/atualiza usuários + vincula à viagem |
| **Import Contacts → Supabase** | Lê a aba Contatos e salva no banco (aparece no app do staff) |
| **🔧 Setup Sheet Headers** | Cria as abas com os cabeçalhos corretos (rodar uma vez na planilha nova) |

---

## Fluxo completo — nova viagem com staff

```
1. Sync Trips                → aba Viagens atualizada com a nova viagem
2. Preencher aba Staff       → adicionar phone, nome, funcao, trip_uuid para cada membro
3. Import Staff → Supabase   → usuários criados com role=staff e vinculados à viagem
4. Preencher aba Contatos    → guias locais, hotéis, emergências da viagem
5. Import Contacts → Supabase→ contatos aparecem na aba Contacts do staff app
6. Staff faz login no app    → cai diretamente na visão de staff com o itinerário real
```

---

## App do staff — o que vê

| Aba | Fonte dos dados |
|---|---|
| **Itinerary** | Fases/atividades in-trip importadas da planilha de viajantes |
| **QR Scan** | Câmera para check-in de viajantes (em desenvolvimento) |
| **Contacts** | Contatos importados da planilha de staff |

O botão **"Traveler view"** no header permite ao staff ver o app exatamente como o viajante vê — útil para conferir o conteúdo antes da viagem.

---

## Diferença entre Staff e Viajante no banco

| Campo | Viajante | Staff |
|---|---|---|
| `users.role` | `traveler` | `staff` |
| `trip_travelers` | Vínculo com a viagem | Vínculo com a viagem (mesmo campo) |
| Origem | WeTravel → webhook | Planilha de Staff → Import |
| Tela no app | Pre-trip / In-trip | Staff app (itinerary, QR, contacts) |
