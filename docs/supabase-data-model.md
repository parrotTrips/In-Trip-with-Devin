# Supabase — Modelo de Dados e Fluxo

## Tabelas

### Autenticação

| Tabela | Colunas principais | Função |
|--------|--------------------|--------|
| `users` | id, phone, full_name, email, role (traveler/staff) | Identidade do usuário |
| `otp_codes` | phone, code, expires_at, used | Códigos OTP temporários para login via SMS |

### Vinculação viajante ↔ viagem

| Tabela | Colunas principais | Função |
|--------|--------------------|--------|
| `trip_travelers` | wetravel_trip_uuid, user_id | Liga um user a uma viagem externa |
| `trip_staff` | wetravel_trip_uuid, user_id, function | Liga usuário staff a uma viagem |
| `traveler_profiles` | trip_traveler_id, passaporte, restrições, etc. | Perfil detalhado — 1:1 com trip_travelers |

### Conteúdo da viagem

| Tabela | Colunas principais | Função |
|--------|--------------------|--------|
| `trip_phases` | wetravel_trip_uuid, phase_type, title, starts_at, ends_at, parent_phase_id | Fases/dias (pre-trip / in-trip), hierárquicas |
| `trip_phase_checklist_items` | trip_phase_id, label, is_required | Itens de checklist de cada fase |
| `trip_phase_links` | trip_phase_id, label, url | Links de recursos por fase |
| `trip_activities` | trip_phase_id, name, activity_type, starts_at, amount_brl | Atividades dentro de cada fase |
| `staff_tasks` | trip_phase_id, assigned_to_user_id, title | Tarefas operacionais do staff por fase |

### Mídia

| Tabela | Colunas principais | Função |
|--------|--------------------|--------|
| `media_assets` | drive_file_id, public_url, mime_type | Referências a arquivos do Google Drive |
| `activity_media` | trip_activity_id, media_asset_id, media_type | Liga mídias a atividades |

### Progresso do viajante

| Tabela | Colunas principais | Função |
|--------|--------------------|--------|
| `traveler_checklist_progress` | trip_traveler_id, trip_phase_checklist_item_id, is_completed | Itens de checklist completados por viajante |
| `traveler_phase_progress` | trip_traveler_id, trip_phase_id, is_completed | Fases completadas por viajante |

---

## Relações entre tabelas

```mermaid
erDiagram
    users {
        uuid id PK
        text phone
        text full_name
        text role
    }
    otp_codes {
        uuid id PK
        text phone
        text code
        bool used
    }
    trip_travelers {
        uuid id PK
        text wetravel_trip_uuid
        uuid user_id FK
    }
    trip_staff {
        uuid id PK
        text wetravel_trip_uuid
        uuid user_id FK
        text function
    }
    traveler_profiles {
        uuid id PK
        uuid trip_traveler_id FK
        text preferred_name
        text passport_number
        bool dietary_restrictions_flag
    }
    trip_phases {
        uuid id PK
        text wetravel_trip_uuid
        uuid parent_phase_id FK
        text phase_type
        text title
        timestamp starts_at
        timestamp ends_at
    }
    trip_phase_checklist_items {
        uuid id PK
        uuid trip_phase_id FK
        text label
        bool is_required
    }
    trip_phase_links {
        uuid id PK
        uuid trip_phase_id FK
        text label
        text url
    }
    trip_activities {
        uuid id PK
        uuid trip_phase_id FK
        text name
        text activity_type
        int duration_minutes
        numeric amount_brl
    }
    staff_tasks {
        uuid id PK
        uuid trip_phase_id FK
        uuid assigned_to_user_id FK
        text title
    }
    media_assets {
        uuid id PK
        text drive_file_id
        text public_url
        text mime_type
    }
    activity_media {
        uuid id PK
        uuid trip_activity_id FK
        uuid media_asset_id FK
        text media_type
    }
    traveler_checklist_progress {
        uuid id PK
        uuid trip_traveler_id FK
        uuid trip_phase_checklist_item_id FK
        bool is_completed
    }
    traveler_phase_progress {
        uuid id PK
        uuid trip_traveler_id FK
        uuid trip_phase_id FK
        bool is_completed
    }

    users ||--o{ trip_travelers : "participa como viajante"
    users ||--o{ trip_staff : "participa como staff"
    users ||--o{ staff_tasks : "responsável por"
    trip_travelers ||--|| traveler_profiles : "tem perfil"
    trip_travelers ||--o{ traveler_checklist_progress : "registra progresso"
    trip_travelers ||--o{ traveler_phase_progress : "registra progresso"
    trip_phases ||--o{ trip_phases : "parent_phase_id"
    trip_phases ||--o{ trip_phase_checklist_items : "contém"
    trip_phases ||--o{ trip_phase_links : "contém"
    trip_phases ||--o{ trip_activities : "contém"
    trip_phases ||--o{ staff_tasks : "contém"
    trip_phase_checklist_items ||--o{ traveler_checklist_progress : "rastreada por"
    trip_phases ||--o{ traveler_phase_progress : "rastreada por"
    trip_activities ||--o{ activity_media : "tem mídia"
    media_assets ||--o{ activity_media : "referenciada por"
```

---

## Fluxo por tela

### Login

```mermaid
sequenceDiagram
    actor Usuário
    participant App
    participant Backend
    participant otp_codes
    participant users

    Usuário->>App: digita telefone
    App->>Backend: POST /auth/request-otp
    Backend->>otp_codes: INSERT código + expires_at
    Backend-->>Usuário: SMS com código

    Usuário->>App: digita código
    App->>Backend: POST /auth/verify-otp
    Backend->>otp_codes: SELECT + marca used=true
    Backend->>users: INSERT ou UPDATE (cria conta se nova)
    Backend-->>App: JWT
```

### HomeScreen

```mermaid
sequenceDiagram
    participant HomeScreen
    participant Backend
    participant trip_travelers
    participant trip_phases
    participant traveler_phase_progress
    participant WeTravel as WeTravel (externo)

    HomeScreen->>Backend: GET /me/trip
    Backend->>trip_travelers: SELECT por user_id
    Backend->>WeTravel: JOIN wetravel_trips (título, datas)
    Backend-->>HomeScreen: dados da viagem

    HomeScreen->>Backend: GET /me/trip/phases
    Backend->>trip_phases: SELECT por wetravel_trip_uuid
    Backend-->>HomeScreen: fases + checklist_items + links

    HomeScreen->>Backend: GET /me/trip/travelers
    Backend->>trip_travelers: SELECT + users
    Backend->>traveler_phase_progress: calcula fase atual de cada viajante
    Backend-->>HomeScreen: lista de viajantes com progresso
```

### PhaseDetails (pre-trip)

```mermaid
sequenceDiagram
    participant PhaseDetails
    participant Backend
    participant trip_phases
    participant trip_phase_checklist_items
    participant traveler_checklist_progress
    participant traveler_phase_progress

    PhaseDetails->>Backend: GET /me/trip/phases/{phase_id}
    Backend->>trip_phases: SELECT fase + checklist_items + links
    Backend-->>PhaseDetails: conteúdo da fase

    PhaseDetails->>Backend: GET /checklist/{trip_id}/{user_id}
    Backend->>traveler_checklist_progress: SELECT por trip_traveler_id
    Backend-->>PhaseDetails: itens completados

    Note over PhaseDetails: viajante marca item
    PhaseDetails->>Backend: POST /checklist/update
    Backend->>traveler_checklist_progress: UPSERT is_completed=true

    Note over PhaseDetails: viajante completa fase
    PhaseDetails->>Backend: POST /phases/complete
    Backend->>traveler_phase_progress: UPSERT is_completed=true
```

### DayDetails (in-trip)

```mermaid
sequenceDiagram
    participant DayDetails
    participant Backend
    participant trip_phases
    participant trip_activities
    participant activity_media
    participant media_assets

    DayDetails->>Backend: GET /me/trip/phases/{phase_id}
    Backend->>trip_phases: SELECT fase do dia
    Backend->>trip_activities: SELECT atividades da fase
    Backend->>activity_media: JOIN media_assets (fotos, vídeos)
    Backend-->>DayDetails: dia com atividades e mídias
```

### ProfileScreen

```mermaid
sequenceDiagram
    participant ProfileScreen
    participant Backend
    participant users
    participant traveler_profiles
    participant WeTravel as WeTravel (externo)

    ProfileScreen->>Backend: GET /profile/{user_id}
    Backend->>users: SELECT dados básicos
    Backend->>traveler_profiles: SELECT perfil detalhado
    Backend->>WeTravel: SELECT pacote e pagamento
    Backend-->>ProfileScreen: perfil completo

    Note over ProfileScreen: usuário edita e salva
    ProfileScreen->>Backend: PUT /profile/{user_id}
    Backend->>users: UPDATE (nome, email)
    Backend->>traveler_profiles: UPSERT (passaporte, restrições, etc.)
```

---

## Origem dos dados: Supabase vs WeTravel

```mermaid
flowchart LR
    subgraph WeTravel["WeTravel (externo)"]
        WT1[wetravel_trips\ntítulo, destino, datas]
        WT2[host_trip_participants\npacote e pagamento]
        WT3[wetravel_participant_phones\ntelefone ↔ viagem]
    end

    subgraph Supabase["Supabase (nosso banco)"]
        SB1[users\nidentidade]
        SB2[trip_travelers\nvínculo viajante↔viagem]
        SB3[trip_phases\nfases e dias]
        SB4[trip_activities\natividades]
        SB5[traveler_profiles\nperfil detalhado]
        SB6[traveler_*_progress\nprogresso]
    end

    WT1 -->|wetravel_trip_uuid| SB2
    WT1 -->|wetravel_trip_uuid| SB3
    WT3 -->|phone| SB1
    SB2 --> SB5
    SB2 --> SB6
    SB3 --> SB4
```
