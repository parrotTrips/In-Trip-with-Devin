# Remoção do Mock e Conexão à API Real

## O que foi feito

Esta sessão removeu completamente o arquivo `tripData.ts` (~612 linhas de dados hardcoded) e conectou todas as telas do app ao backend real. Também criou a infraestrutura para popular o banco e alternar entre usuários de teste.

---

## Contexto

O frontend tinha uma camada de mock (`src/data/tripData.ts`) com:
- 14 viajantes com avatares e fase atual
- 4 fases pré-viagem (Visa, Vaccination, Packing, Documents) com checklists e links
- 10 dias de viagem com atividades detalhadas
- Constantes hardcoded: `tripName`, `tripDates`, `currentUserPhaseId`, `parrotPhaseId`

O backend tinha as tabelas certas (`trip_phases`, `trip_activities`, `trip_phase_checklist_items`, `trip_phase_links`) mas **estavam vazias**. Os dados do mock eram placeholder — a viagem real será diferente.

A decisão foi: popular o banco com os dados placeholder agora, conectar o frontend à API, e substituir pelo conteúdo real quando estiver disponível.

---

## Arquivos novos e alterados

### Backend

**`backend/scripts/seed_placeholder_trip.py`** — Script de seed idempotente.
- Recebe `--trip-uuid` e `--start-date` via CLI
- Insere 14 fases, 31 checklist items, links e 26 atividades no banco
- Cria 2 usuários de teste (`+15550000001`, `+15550000002`) e os vincula ao trip
- Gera JWTs válidos para os usuários de teste
- Imprime no terminal o conteúdo pronto para salvar em `frontend/src/config/devUsers.ts`

**`backend/app/services/trip_service.py`** — Service novo com 3 funções:
- `get_trip_phases(user_id, session)` — retorna todas as fases visíveis da viagem com checklist items e links embutidos
- `get_trip_phase_detail(user_id, phase_id, session)` — retorna uma fase específica com atividades
- `get_trip_travelers(user_id, session)` — retorna todos os viajantes do mesmo trip com fase atual de cada um (derivada do `traveler_phase_progress`)

**`backend/app/routers/trip.py`** — 3 novos endpoints adicionados ao router existente:
- `GET /me/trip/phases` — lista de fases com checklist e links
- `GET /me/trip/phases/{phase_id}` — detalhe de uma fase com atividades
- `GET /me/trip/travelers` — viajantes do trip com fase atual

### Frontend

**`src/features/trip/services/trip-api.ts`** — Atualizado com novos tipos e funções:
- `TripPhase`, `TripPhaseDetail`, `Activity`, `ChecklistItem`, `PhaseLink`, `TripTraveler` — tipos que espelham a resposta da API
- `getMyTripPhases()`, `getMyTripPhaseDetail(phaseId)`, `getMyTripTravelers()` — novas funções

**`src/app/providers/trip-context.ts`** + **`TripProvider.tsx`** — Contexto global de viagem:
- Busca `/me/trip` + `/me/trip/phases` + `/me/trip/travelers` em paralelo ao montar
- Expõe `{ tripInfo, phases, travelers, loading, error, refetch }` via `useTripContext()`
- Wrappeia o `AppRouter` dentro do `App.tsx` (só para usuários logados como traveler)

**`src/features/trip/pages/HomeScreen.tsx`** — Reescrito sem mock:
- Usa `useTripContext()` para fases e viajantes
- `currentUserPhaseId` vem dos viajantes (match por `user.userId`)
- `parrotPhaseId` calculado dinamicamente: fase in-trip com `starts_at` mais próximo de hoje
- Estados de loading (spinner) e erro (tela com mensagem) explícitos
- Avatares dos viajantes são iniciais do nome (sem URLs de imagem hardcoded)

**`src/features/trip/pages/PhaseDetails.tsx`** — Reescrito:
- Busca `GET /me/trip/phases/{phaseId}` ao montar
- `TRIP_ID = 'ross26'` removido — usa `tripInfo.wetravel_trip_uuid` do TripContext
- Checklist usa `item.label` (não mais `item.text` do mock)
- Erro real se fase não encontrada

**`src/features/trip/pages/DayDetails.tsx`** — Reescrito:
- Busca `GET /me/trip/phases/{dayId}` ao montar
- Activities vêm da API (type: `Activity` com `activity_type`, `short_description`, `practical_info`)
- Horário formatado a partir de `starts_at` (ISO) + `duration_minutes`
- Album sem mock (placeholder estático)

**`src/shared/components/ProgressBar.tsx`** — Agora recebe props:
- `{ totalPhases, currentPhaseOrder, parrotPhaseOrder }`
- Sem imports de mock

**`src/features/dev/DevUserSwitcher.tsx`** — Novo componente:
- Botão 🛠️ flutuante só em `import.meta.env.DEV`
- Lê `src/config/devUsers.ts` (gitignored, gerado pelo seed script)
- Ao clicar num usuário: chama `login()` do AuthContext + `refetch()` do TripContext
- Sem esse arquivo, o componente não aparece (graceful fallback)

**`src/config/devUsers.example.ts`** — Arquivo de exemplo com a estrutura esperada.

**Deletados:**
- `src/data/tripData.ts`
- `src/features/trip/data/tripData.ts`

---

## Como usar

### 1. Rodar o seed

```bash
cd backend
env/bin/python3 scripts/seed_placeholder_trip.py \
  --trip-uuid <uuid-de-uma-viagem-real-em-wetravel_trips> \
  --start-date 2026-02-27
```

O script imprime no terminal o conteúdo para salvar em `frontend/src/config/devUsers.ts`.

### 2. Salvar o devUsers

Copiar o output do script para:
```
frontend/src/config/devUsers.ts
```
Esse arquivo está no `.gitignore` — nunca commitar (contém tokens JWT).

### 3. Rodar o app

```bash
cd frontend && npm run dev
```

O botão 🛠️ aparece no canto inferior direito. Clicar para alternar entre os 2 usuários de teste sem reiniciar o servidor.

---

## Comportamento em caso de erro de API

Diferente do comportamento anterior (fallback silencioso para mock), agora:
- **HomeScreen**: spinner durante loading, tela de erro com mensagem se falhar
- **PhaseDetails** / **DayDetails**: spinner + tela de erro com botão "Voltar"
- **ProgressBar**: retorna `null` se `totalPhases === 0` (não quebra o layout)

---

## Estrutura dos dados no banco

### `trip_phases`
| campo | descrição |
|-------|-----------|
| `wetravel_trip_uuid` | vincula ao trip |
| `phase_type` | `"pre-trip"` ou `"in-trip"` |
| `title` | ex: `"Day 1 — Feb 27"` |
| `subtitle` | ex: `"Arrival in Rio"` |
| `icon` | chave do iconMap: `"passport"`, `"plane-landing"`, etc |
| `sort_order` | 0–13 (pre-trip: 0–3, in-trip: 4–13) |
| `starts_at` | data/hora do dia (só para fases in-trip) |

### `trip_activities`
| campo | descrição |
|-------|-----------|
| `trip_phase_id` | FK para `trip_phases` |
| `activity_type` | `"included"`, `"optional"`, `"suggested"`, `"logistics"` |
| `starts_at` | horário da atividade (opcional) |
| `duration_minutes` | duração em minutos (opcional) |
| `short_description` | texto principal exibido no card |
| `practical_info` | texto expandido (detalhes, dicas) |
| `amount_brl` | preço em R$ para atividades opcionais |

---

## Quando substituir pelos dados reais

Quando você tiver o conteúdo real de uma viagem:

1. Rodar o seed script apontando para o `wetravel_trip_uuid` real
2. Ajustar as fases/atividades diretamente no banco (Supabase dashboard ou novo script)
3. Nenhuma mudança de código necessária — o app lerá os dados atualizados automaticamente

Os usuários reais já devem ter entrada em `trip_travelers` (criada via onboarding ou manualmente). O seed só popula o **conteúdo** da viagem (fases/atividades), não os viajantes reais.

---

## Pendências / próximos passos

- **`practical_info` das atividades**: o seed atual não popula esse campo (omitido por brevidade). Pode ser adicionado depois diretamente no banco ou via update no script.
- **Imagens das atividades**: `trip_activities` não tem campo de imagem ainda. As imagens do mock não foram migradas. A tabela `media_assets` + `activity_media` existem no schema mas ainda não são usadas pelo frontend.
- **Album colaborativo**: DayDetails tem o card "Group Album" mas sem funcionalidade real (upload ainda não implementado).
- **Fase atual do usuário**: derivada do `traveler_phase_progress`. Enquanto não houver progresso gravado, todos os viajantes aparecem na primeira fase.
- **Dados reais da viagem**: o conteúdo das fases e atividades ainda é placeholder. Substituir quando o conteúdo real estiver pronto.
