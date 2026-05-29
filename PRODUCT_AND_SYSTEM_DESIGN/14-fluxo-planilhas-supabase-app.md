# Fluxo: Planilhas → Supabase → Aplicativo

Documento de referência para entender como o conteúdo de uma viagem sai de uma planilha Google Sheets e chega na tela do viajante.

---

## Visão geral

O sistema tem três camadas principais:

1. **Google Sheets** — onde a equipe Parrot Trips escreve o conteúdo das viagens
2. **Supabase (PostgreSQL)** — banco de dados que armazena tudo de forma estruturada
3. **Aplicativo** — o que o viajante vê e com o qual interage

A comunicação entre essas camadas é feita por scripts Python rodados manualmente pela equipe:
- `create_trip_sheets.py` — cria a planilha estruturada no Drive
- `import_trip_content.py` — lê a planilha preenchida e envia os dados para o Supabase

---

## Fluxo 1 — Criação e preenchimento da planilha

Este fluxo acontece uma vez por temporada, quando novas viagens são cadastradas.

```mermaid
flowchart TD
    A([Equipe cadastra viagem no WeTravel]) --> B[WeTravel importa trip_uuid para wetravel_trips no Supabase]
    B --> C[Equipe roda create_trip_sheets.py]
    C --> D{Planilha ja existe no Drive?}
    D -- Sim --> E([Pula — nada a fazer])
    D -- Nao --> F[Cria planilha Parrot Trips — Conteudo de Viagens no Google Drive]
    F --> G[Gera 5 abas estruturadas com exemplos por viagem]
    G --> H([Planilha pronta para preenchimento])
```

### As 5 abas da planilha

| Aba | Conteúdo | Importada? |
|---|---|---|
| **Viagens** | Lista de trip_uuid, nome e datas | Não — só referência |
| **Fases** | Uma linha por fase pré-trip (visa, vacinas, mala, docs...) | Sim |
| **Checklist** | Uma linha por item de checklist | Sim |
| **Links** | Uma linha por link útil | Sim |
| **Roteiro** | Uma linha por atividade de cada dia | Sim |

Cada aba tem `trip_uuid` como primeira coluna para identificar a qual viagem cada linha pertence.

---

## Fluxo 2 — Importação para o Supabase

Este fluxo acontece sempre que o conteúdo de uma viagem é finalizado ou atualizado na planilha.

```mermaid
flowchart TD
    A([Equipe preenche a planilha no Sheets]) --> B[Equipe roda import_trip_content.py com --trip-uuid X ou --all]
    B --> C[Script autentica no Google Sheets via OAuth2]
    C --> D[Le abas Fases, Checklist, Links, Roteiro]
    D --> E[Filtra linhas pelo trip_uuid]
    E --> F{Ja existem dados no banco?}
    F -- Sim --> G[Apaga tudo do trip: fases, checklist, links, atividades, progresso dos viajantes]
    F -- Nao --> H
    G --> H[Insere dados frescos em trip_phases, checklist_items, links, activities]
    H --> I([Conteudo disponivel no aplicativo])
```

### O que é apagado e reinserido a cada import

O import é **destrutivo e idempotente** — pode rodar quantas vezes quiser com o mesmo resultado final:

```
trip_phases
  -> trip_phase_checklist_items
  -> trip_phase_links
  -> trip_activities
  -> traveler_checklist_progress  (progresso dos viajantes)
  -> traveler_phase_progress      (progresso dos viajantes)
```

> Atencao: Rodar o import apaga o progresso salvo dos viajantes para aquela viagem. Fazer isso depois que viajantes ja comecaram a usar o app vai resetar o progresso deles.

---

## Fluxo 3 — O viajante usa o aplicativo (pré-viagem)

Durante o período pré-viagem, o viajante vai marcando as tarefas conforme se prepara.

```mermaid
flowchart TD
    A([Viajante abre o app]) --> B[App busca fases da viagem GET /me/trip/phases]
    B --> C[App busca progresso do checklist e das fases]
    C --> D[Exibe barra de progresso so com fases pre-trip]
    D --> E[Viajante navega nas fases pre-viagem]
    E --> F[Viajante marca um item do checklist]
    F --> G[POST /checklist/update - Salva em traveler_checklist_progress]
    G --> H[Viajante marca a fase como completa]
    H --> I[POST /phases/complete - Salva em traveler_phase_progress]
    I --> J[Barra de progresso avanca]
    J --> E
```

---

## Fluxo 4 — Reset antes da viagem + modo in-trip

Uma semana antes da viagem, a equipe reseta o progresso para que o passarinho comece do zero no roteiro.

```mermaid
flowchart TD
    A([Cerca de 1 semana antes da partida]) --> B[Equipe roda reset_traveler_progress.py com --trip-uuid X]
    B --> C[Apaga traveler_checklist_progress e traveler_phase_progress para todos os viajantes da viagem]
    C --> D([Passarinho zerado])
    D --> E([Dia da viagem: starts_at do Dia 1 menor ou igual a hoje])
    E --> F[Backend calcula automaticamente: fases in-trip com starts_at menor ou igual a hoje sao marcadas como completas]
    F --> G[App exibe barra de progresso so com fases in-trip]
    G --> H[Barra avanca automaticamente conforme os dias passam]
    H --> I([Viajante acompanha o progresso da viagem])
```

### Como o avanço automático funciona

Não há nenhuma ação manual necessária durante a viagem. A lógica é:

```
Para cada fase in-trip:
  se starts_at <= agora  ->  fase completa (calculado no backend, nao salvo no banco)
  se starts_at > agora   ->  fase pendente
```

O `current_phase_id` de cada viajante é o primeiro dia que ainda não começou — ou seja, o próximo dia da viagem.

---

## Fluxo 5 — Atualização de conteúdo em produção

Quando é necessário corrigir ou atualizar o conteúdo de uma viagem que já está no ar.

```mermaid
flowchart TD
    A([Erro detectado no conteudo]) --> B[Editar a planilha no Google Sheets]
    B --> C{Viajantes ja comecaram a usar?}
    C -- Nao --> D[Rodar import com --trip-uuid X]
    C -- Sim --> E[Avaliar impacto: import vai apagar progresso dos viajantes]
    E --> F{Vale a pena perder o progresso?}
    F -- Sim --> D
    F -- Nao --> G([Deixar como esta ou corrigir direto no banco via SQL])
    D --> H([Conteudo atualizado no app])
```

---

## Estrutura de dados no Supabase

```mermaid
erDiagram
    wetravel_trips {
        string trip_uuid PK
        string title
        date start_date
        date end_date
    }

    trip_travelers {
        uuid id PK
        string wetravel_trip_uuid FK
        uuid user_id FK
    }

    trip_phases {
        uuid id PK
        string wetravel_trip_uuid FK
        string phase_type
        string title
        int sort_order
        datetime starts_at
    }

    trip_phase_checklist_items {
        uuid id PK
        uuid trip_phase_id FK
        string label
        bool is_required
        int sort_order
    }

    trip_phase_links {
        uuid id PK
        uuid trip_phase_id FK
        string label
        string url
    }

    trip_activities {
        uuid id PK
        uuid trip_phase_id FK
        string name
        string activity_type
        int sort_order
    }

    traveler_checklist_progress {
        uuid trip_traveler_id FK
        uuid trip_phase_checklist_item_id FK
        bool is_completed
    }

    traveler_phase_progress {
        uuid trip_traveler_id FK
        uuid trip_phase_id FK
        bool is_completed
    }

    wetravel_trips ||--o{ trip_travelers : "tem viajantes"
    wetravel_trips ||--o{ trip_phases : "tem fases"
    trip_phases ||--o{ trip_phase_checklist_items : "tem checklist"
    trip_phases ||--o{ trip_phase_links : "tem links"
    trip_phases ||--o{ trip_activities : "tem atividades"
    trip_travelers ||--o{ traveler_checklist_progress : "tem progresso"
    trip_travelers ||--o{ traveler_phase_progress : "tem progresso"
```

---

## Resumo dos scripts disponíveis

| Script | Quando usar | Comando |
|---|---|---|
| `create_trip_sheets.py` | Ao adicionar novas viagens — cria estrutura na planilha | `poetry run python scripts/create_trip_sheets.py --folder-id ID --use-adc` |
| `import_trip_content.py` | Após preencher a planilha — envia para o Supabase | `poetry run python scripts/import_trip_content.py --all` |
| `reset_traveler_progress.py` | Cerca de 1 semana antes da viagem — zera progresso dos viajantes | `poetry run python scripts/reset_traveler_progress.py --trip-uuid X` |
| `reset_trip_content.py` | Para apagar fases e atividades do banco e recomeçar do zero | `poetry run python scripts/reset_trip_content.py --trip-uuid X` |

---

## Calendário operacional sugerido

```mermaid
timeline
    title Ciclo de vida de uma viagem
    section Pre-operacao
        N-90 dias : Cadastrar viagem no WeTravel
                  : Rodar create_trip_sheets.py
        N-60 dias : Preencher planilha com conteudo real
                  : Rodar import_trip_content.py
        N-30 dias : Revisar e corrigir conteudo
                  : Re-rodar import se necessario
    section Pre-viagem
        N-7 dias  : Rodar reset_traveler_progress.py
                  : Viajantes com progresso zerado
    section In-trip
        Dia 1     : starts_at do Dia 1 menor ou igual a hoje
                  : Barra muda para modo in-trip
                  : Progresso avanca automaticamente
    section Pos-viagem
        Fim       : Viagem encerrada
```
