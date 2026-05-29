# Inserção de Conteúdo das Viagens — Google Sheets + Import Script

Decisão de arquitetura e guia operacional para preencher o conteúdo das viagens (fases pré-trip, roteiro dia a dia, atividades) usando Google Sheets como fonte de dados e um script Python de importação como pipeline de entrada no banco.

---

## Decisão de arquitetura

**Abordagem adotada:** Uma planilha Google Sheets centralizada → script de importação por viagem → banco Supabase.

| critério | Google Sheets | Interface de admin |
|---|---|---|
| Tempo de construção | 0 (Sheets já existe) | 1–2 semanas de dev |
| Colaboração | Múltiplos editores simultâneos, comentários, histórico | Requer RBAC, auth de staff |
| Flexibilidade de edição | Copiar/colar, fórmulas, bulk edit | CRUD linha a linha |
| Curva de aprendizado para o time | Zero | Treinamento necessário |
| Quando faz sentido migrar | — | Quando o volume tornar o fluxo manual ineficiente |

**Conclusão:** Uma planilha centralizada resolve 100% das necessidades atuais. A migração para interface admin vira tarefa quando o volume de viagens tornar o fluxo Sheets→importação gargalo.

---

## Estrutura da planilha

Uma única planilha chamada **`Parrot Trips — Conteúdo de Viagens`** na [pasta do Drive](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP).

Todas as viagens ficam na mesma planilha. O `trip_uuid` é a primeira coluna em cada aba — o script filtra as linhas pelo uuid da viagem que está sendo importada.

---

### Aba 1: `Pre-Trip`

Uma linha por campo de conteúdo. Primeira coluna é `trip_uuid`.

**Colunas:**

| coluna | tipo | exemplo |
|---|---|---|
| `trip_uuid` | texto | `gsb-nye-2026` |
| `fase` | texto | `visa` / `vaccination` / `packing` / `documents` |
| `bloco` | texto | `header` / `checklist` / `link` |
| `ordem` | número | `1`, `2`, `3`… (dentro do bloco) |
| `campo` | texto | `title` / `subtitle` / `icon` / `short_description` / `detailed_description` / `label` / `url` / `is_required` |
| `valor` | texto | o conteúdo em si |

**Exemplo de linhas:**

| trip_uuid | fase | bloco | ordem | campo | valor |
|---|---|---|---|---|---|
| gsb-nye-2026 | visa | header | 1 | title | Visto |
| gsb-nye-2026 | visa | header | 1 | subtitle | Tudo que você precisa saber sobre visto para o Brasil |
| gsb-nye-2026 | visa | checklist | 1 | label | Verificar se sua nacionalidade requer visto |
| gsb-nye-2026 | visa | checklist | 1 | is_required | true |
| gsb-nye-2026 | visa | link | 1 | label | Portal eVisa Brasil |
| gsb-nye-2026 | visa | link | 1 | url | https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos |

---

### Aba 2: `Roteiro`

Uma linha por atividade. Primeira coluna é `trip_uuid`. As colunas `dia_*` se repetem em todas as linhas do mesmo dia (o script deduplica ao criar as fases).

**Colunas:**

| coluna | obrigatório | tipo | exemplo |
|---|---|---|---|
| `trip_uuid` | ✅ | texto | `gsb-nye-2026` |
| `dia` | ✅ | número | `1` |
| `data` | ✅ | data | `2026-12-26` |
| `dia_titulo` | ✅ | texto | `Day 1 — Dec 26` |
| `dia_subtitulo` | — | texto | `Chegada ao Rio` |
| `dia_icon` | — | texto | `plane-landing` |
| `dia_descricao_curta` | ✅ | texto | `Transfer, check-in e Welcome Happy Hour` |
| `dia_descricao_completa` | — | texto | Texto longo do dia |
| `atividade_nome` | ✅ | texto | `Transfer do Aeroporto` |
| `atividade_tipo` | ✅ | texto | `included` / `optional` / `suggested` / `logistics` |
| `atividade_horario` | — | hora | `10:00` |
| `atividade_duracao_min` | — | número | `120` |
| `atividade_descricao_curta` | ✅ | texto | `Recepção no aeroporto conforme pré-viagem` |
| `atividade_info_pratica` | — | texto | `Procurar placa Parrot Trips. Levar documento.` |
| `atividade_preco_brl` | só para opcional | número | `150` |

---

## Scripts

### `create_trip_sheets.py` — criar a planilha

Cria a planilha única no Drive com as duas abas estruturadas e uma seção de exemplo por viagem cadastrada no banco. É idempotente: pula se a planilha já existir.

```bash
cd backend
poetry run python scripts/create_trip_sheets.py \
  --folder-id 1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP \
  --use-adc

# Também apaga as planilhas antigas da pasta:
poetry run python scripts/create_trip_sheets.py \
  --folder-id 1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP \
  --use-adc --clean-old
```

Ao final, o script imprime o Sheet ID. Adicionar ao `backend/.env`:
```
TRIP_CONTENT_SHEET_ID=<id_impresso>
```

---

### `import_trip_content.py` — importar uma viagem

Lê a planilha centralizada, filtra as linhas do `trip_uuid` especificado e faz um replace completo no banco (apaga tudo do trip e insere de novo).

```bash
cd backend
poetry run python scripts/import_trip_content.py --trip-uuid gsb-nye-2026
```

O Sheet ID é lido automaticamente de `TRIP_CONTENT_SHEET_ID` no `.env`. Para sobrescrever:
```bash
poetry run python scripts/import_trip_content.py --trip-uuid gsb-nye-2026 --sheet-id <outro_id>
```

---

### `reset_trip_content.py` — limpar o banco

Apaga todos os dados de `trip_phases` e filhos (activities, checklist, links, progress) para uma viagem ou para todas.

```bash
# Dry run:
poetry run python scripts/reset_trip_content.py --dry-run

# Apagar tudo (pede confirmação):
poetry run python scripts/reset_trip_content.py

# Apagar só uma viagem:
poetry run python scripts/reset_trip_content.py --trip-uuid gsb-nye-2026
```

---

## Cadência de atualização

| cenário | ação |
|---|---|
| Edição no Sheets | Rodar `import_trip_content.py --trip-uuid <uuid>` |
| Correção de erro no conteúdo | Editar a célula no Sheets → rodar o import |
| Nova viagem cadastrada no WeTravel | Rodar `create_trip_sheets.py` — ele adiciona a nova viagem na planilha |
| Conteúdo urgente (prod) | Mesmo fluxo — o banco em prod é o Supabase, o script conecta direto |

Não há sincronização automática. O time roda o script quando o conteúdo está pronto ou quando há correção.

---

## Quando migrar para uma interface de admin

Sinais de que o Sheets→script virou gargalo:

- O time está editando 3+ viagens ao mesmo tempo e perde controle de qual versão está no banco
- Há necessidade de preview em tempo real do conteúdo
- Editores não técnicos ficam com medo de "quebrar algo" ao rodar o script
- É necessário aprovação/review antes de publicar mudanças

**Quando isso acontecer**, a migração é uma tela de admin no próprio app (rota `/admin/trips`) com formulários de edição direto no banco. O backend já está preparado — os modelos e endpoints existem.

---

## Status atual (Mai 2026)

| viagem | viajantes no banco | conteúdo | prioridade |
|---|---|---|---|
| K-LATAM 26 Brazil Trek | ⚠️ 0 | ⚠️ sem conteúdo | baixa (sem viajantes) |
| YSOM Brazil Trek 26 | ⚠️ 0 | ⚠️ sem conteúdo | baixa (sem viajantes) |
| **GSB NYE Brazil Trek** | ✅ 35 | ⚠️ sem conteúdo | **🔥 alta — mais próxima com viajantes** |
| HBS Diaspora Brazil Trek | ⚠️ 0 | ⚠️ sem conteúdo | baixa (sem viajantes) |
| Wharton Carnaval Trek 2027 | ✅ 45 | ⚠️ sem conteúdo | média |
| UCLA Carnival 27 Trek | ✅ 47 | ⚠️ sem conteúdo | média |
| Wharton Brazil Trek Dec 2026 | ✅ 26 | ⚠️ sem conteúdo | média |

**Próximo passo concreto:** preencher a planilha para a **GSB NYE (26 Dez)** e rodar o import.
