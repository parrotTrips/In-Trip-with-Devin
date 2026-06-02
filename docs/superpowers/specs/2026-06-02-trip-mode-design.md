# Trip Mode (Pre-Trip / In-Trip) — Design

**Data:** 2026-06-02
**Status:** Aprovado

---

## Contexto

Hoje o app decide qual modo exibir (pre-trip vs in-trip) comparando a data atual com `start_date` da viagem. Isso causa dois problemas:

1. A equipe não controla quando a transição acontece — ela é automática e imprevisível do ponto de vista operacional
2. A barra in-trip pode passar de 100% se a viagem terminou mas ainda está no app

O novo design dá à equipe controle explícito: **rodar o reset de progresso é o evento que marca a transição de pre-trip para in-trip**. O modo fica armazenado no banco e o frontend o consome diretamente.

---

## Requisitos

1. **Nova tabela `trip_settings`** — armazena o modo atual de cada viagem
2. **Reset de progresso muda o modo para `"in-trip"`** — automático, sem passo extra para a equipe
3. **Frontend usa `trip_mode` do backend** — não mais `start_date`
4. **Legenda "Pre-Trip" / "In-Trip"** — exibida próxima à barra de progresso
5. **Barra in-trip limitada a 100%** — mesmo após o último dia ter passado
6. **`Code.gs` atualizado** — o botão Reset Traveler Progress documenta que muda o modo
7. **Novo endpoint `POST /admin/trips/set-mode`** — permite reverter manualmente se necessário

---

## Banco de Dados

### Nova tabela: `trip_settings`

```sql
CREATE TABLE trip_settings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_uuid   TEXT NOT NULL UNIQUE,
    mode        TEXT NOT NULL DEFAULT 'pre-trip',  -- 'pre-trip' | 'in-trip'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Semântica:** Se não existe registro para uma viagem, o modo padrão é `"pre-trip"`. O backend usa `COALESCE` ou LEFT JOIN com fallback.

### Migração Alembic

Um novo arquivo de migração cria a tabela. Não altera nenhuma tabela existente.

---

## Backend

### Model SQLAlchemy: `TripSettings`

Novo model em `backend/app/db/models/trip.py` (ou arquivo separado `trip_settings.py`).

```python
class TripSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_settings"
    trip_uuid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="pre-trip")
```

### `admin_service.py` — atualizar `admin_reset_progress`

Após deletar o progresso, criar ou atualizar `trip_settings` com `mode = "in-trip"`:

```python
async def admin_reset_progress(trip_uuid: str) -> dict:
    # ... deleta traveler_checklist_progress e traveler_phase_progress ...
    # + seta modo in-trip:
    await conn.execute(
        """
        INSERT INTO trip_settings (trip_uuid, mode)
        VALUES ($1, 'in-trip')
        ON CONFLICT (trip_uuid) DO UPDATE SET mode = 'in-trip', updated_at = now()
        """,
        trip_uuid,
    )
    return {
        "status": "ok",
        "trip_uuid": trip_uuid,
        "mode": "in-trip",
        "deleted_checklist_progress": deleted_checklist,
        "deleted_phase_progress": deleted_phase,
    }
```

### Novo endpoint: `POST /admin/trips/set-mode`

Para reverter manualmente (ex: voltar para pre-trip após um erro):

```python
class SetModeRequest(BaseModel):
    trip_uuid: str
    mode: Literal["pre-trip", "in-trip"]

@router.post("/trips/set-mode")
async def set_trip_mode(body: SetModeRequest):
    result = await admin_set_mode(body.trip_uuid, body.mode)
    return result
```

### `trip_service.py` — incluir `trip_mode` nas respostas

`get_trip_phases` e `GET /me/trip` passam a ler `trip_settings` e incluir `trip_mode` na resposta:

```python
# No GET /me/trip → trip dict inclui:
"trip_mode": "pre-trip"  # ou "in-trip"

# No GET /me/trip/phases → resposta inclui:
"trip_mode": "pre-trip"  # ou "in-trip"
```

O `trip_mode` é lido com LEFT JOIN ou query separada — se não existe registro em `trip_settings`, retorna `"pre-trip"` como padrão.

---

## Frontend

### `trip-api.ts` — adicionar `trip_mode` às interfaces

```typescript
interface TripInfo {
  // ... campos existentes ...
  trip_mode: 'pre-trip' | 'in-trip';
}
```

### `HomeScreen.tsx` — substituir `tripStarted` por `trip_mode`

Antes:
```typescript
const tripStarted = tripInfo
  ? new Date(tripInfo.start_date + 'T00:00:00') <= new Date()
  : false;
```

Depois:
```typescript
const isInTrip = tripInfo?.trip_mode === 'in-trip';
```

Todas as referências a `tripStarted` passam a usar `isInTrip`.

### Legenda "Pre-Trip" / "In-Trip" na barra

A legenda já existe no Phase Labels (linha com bolinhas coloridas). Adicionar próximo à barra de progresso no hero:

```tsx
<span className="text-xs text-emerald-100 mt-1">
  {isInTrip ? '🗺 In-Trip' : '📋 Pre-Trip'}
</span>
```

### Barra in-trip limitada a 100%

Hoje: `dateBasedCount = progressPhases.filter(starts_at <= now).length`

Quando todos os dias passam: `dateBasedCount = totalPhases` → já é 100%. Mas para garantir que nunca ultrapasse por algum edge case:

```typescript
const userCompletedCount = isInTrip
  ? Math.min(dateBasedCount, totalPhases)
  : completedCount;
```

---

## `google-apps-script/Code.gs`

### Atualizar `resetProgress`

O texto do dialog de confirmação muda para deixar claro que o modo também muda:

```javascript
var confirm = ui.alert(
  "⚠️ Reset Traveler Progress → Switch to In-Trip",
  "This will:\n• RESET the progress bar of all travelers\n• Switch the trip mode to IN-TRIP\n\nThe progress bar will now advance automatically as trip days pass.\n\nContinue?",
  ui.ButtonSet.YES_NO
);
```

### Adicionar item de menu "Set Mode (Advanced)"

Para uso manual se necessário reverter:

```javascript
.addItem("Set Trip Mode (Pre-Trip / In-Trip)", "setTripMode")
```

```javascript
function setTripMode() {
  var ui = SpreadsheetApp.getUi();
  var trips = getTripList();
  if (!trips || trips.length === 0) return;
  var modeRes = ui.prompt(
    "🦜 Set Trip Mode",
    "Type the trip_uuid and mode separated by space:\nExample: gsb-nye-2026 pre-trip\n\nModes: pre-trip | in-trip\n\n" +
    trips.map(function(t, i) { return (i+1) + ". " + t.name + " → " + t.uuid; }).join("\n"),
    ui.ButtonSet.OK_CANCEL
  );
  if (modeRes.getSelectedButton() !== ui.Button.OK) return;
  var parts = modeRes.getResponseText().trim().split(" ");
  if (parts.length < 2) { ui.alert("Invalid input."); return; }
  var trip_uuid = parts[0];
  var mode = parts[1];
  try {
    var result = callBackend("/admin/trips/set-mode", null, { trip_uuid: trip_uuid, mode: mode });
    ui.alert("✅ Mode set to '" + result.mode + "' for trip " + trip_uuid);
  } catch(e) {
    ui.alert("❌ Error: " + e.message);
  }
}
```

Note: `callBackend` precisará de um overload para aceitar body customizado — ou criar `callBackendWithBody(endpoint, body)`.

---

## Fluxo operacional completo

```
Viagem entra no sistema → modo "pre-trip" (padrão)
↓
Viajantes usam o app, marcam fases, barra avança
↓
Equipe decide iniciar in-trip (1 semana antes, 1 dia antes, ou no dia)
↓
Clica em "Reset Traveler Progress" na planilha → confirma
↓
Backend: apaga progresso + seta mode = "in-trip" em trip_settings
↓
App exibe "🗺 In-Trip", barra avança pelos dias automaticamente
↓
Último dia passa → barra fica em 100% para sempre (até viagem ser removida)
```

---

## Spec Self-Review

**Placeholder scan:** Nenhum TBD encontrado.

**Consistência interna:**
- `trip_mode` retornado pelo backend → consumido pelo frontend como `isInTrip` ✅
- `admin_reset_progress` → chama `admin_set_mode("in-trip")` internamente ✅
- `callBackend` no Apps Script precisa suportar body customizado para `set-mode` — explicitado ✅
- `Math.min(dateBasedCount, totalPhases)` garante max 100% ✅

**Escopo:** Focado, implementável em um único ciclo de plan → implement.
