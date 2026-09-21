# Content Console — Plataforma de Conteúdo (Fatia A) — Design

**Data:** 2026-09-21
**Status:** Aprovado

---

## Contexto

Hoje todo o conteúdo operacional das viagens é digitado em uma planilha Google e importado para o Supabase pelo menu Apps Script (`🦜 Parrot Trips → Export Trip Content to App`). Esse caminho vem produzindo falhas que são estruturais, não acidentais:

1. **Sem campo obrigatório.** Linhas de conteúdo salvas com a coluna `trip_uuid` em branco são silenciosamente descartadas por `filter_rows_by_trip`, e o import responde `"No data found for trip X"` — um erro genérico, longe da causa.
2. **Sem integridade referencial.** Um `fase` digitado na aba Checklist que não existe na aba Fases é descartado sem aviso.
3. **Import destrutivo.** `write_to_db` apaga todas as fases e atividades da viagem e recria com IDs novos. Toda reimportação destrói check-ins, participantes e tarefas de staff vinculados às atividades antigas.
4. **Sem rastro.** A planilha não registra quem alterou o quê, nem quando.

A decisão é **parar de usar planilha como entrada** e construir uma plataforma própria (o *console*), desenhada em torno das informações que já existem no app. As planilhas permanecem funcionando exatamente como hoje e passam a ser, na prática, apenas leitura.

Esta é a **fatia A** de quatro. As demais (Roteiro, Informações, Staff) repetirão o padrão estabelecido aqui.

---

## Decisões tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Papel das planilhas | Intocadas; leitura na prática | Nada de migração destrutiva nem conflito de escrita |
| Primeira fatia | Fases + Checklist + Links | É o núcleo ("jogo da vida") e o caso mais difícil: hierarquia e ordenação |
| Onde vive | App Vite separado, deploy próprio | Isolamento total do app do viajante |
| Publicação | Rascunho + publicar, com a **fase** como unidade | Menor custo: `is_visible` já existe e já é filtrado |
| Acesso | Papel `admin` único, login WhatsApp OTP | Time pequeno; evita sistema de permissões que ninguém pediu |
| Link de pré-embarque | Botão de copiar URL existente | O deep link já funciona hoje |
| Criação de viagens | Fora de escopo | Viagens continuam vindo do WeTravel |

---

## Requisitos

1. **App separado** (`console/`), com build e deploy independentes do app do viajante.
2. **Login por WhatsApp OTP**, reusando os endpoints `/auth` existentes.
3. **Papel `admin`**, novo valor em `users.role`, exigido em todos os endpoints do console.
4. **CRUD de fases pré-trip**, com checklist e links aninhados.
5. **Rascunho e publicação por fase**, sem que rascunho apareça para viajante ou staff.
6. **Reordenação** de fases, itens de checklist e links.
7. **Botão de copiar o link de pré-embarque** da viagem.
8. **Nenhuma alteração** no app do viajante, no Apps Script ou nos endpoints `/admin`.

---

## Arquitetura

Três peças, todas aditivas:

| Peça | O que é | Altera o que existe? |
|---|---|---|
| `console/` | App Vite/React novo, Netlify próprio | Não — projeto novo |
| `/console/*` | Router FastAPI novo, JWT + `role=admin` | Não — `/admin` permanece como está |
| Papel `admin` | Novo valor em `users.role` | Aditivo (hoje: `traveler \| staff`) |

`users.role` é uma coluna `Text` sem CHECK constraint (verificado no banco), então aceitar o valor `admin` não exige migration.

### Por que um prefixo novo em vez de `/admin`

`backend/app/middleware/auth.py:14` declara:

```python
_PUBLIC_PREFIXES = ("/auth", "/admin")
```

Todo o prefixo `/admin` **pula o middleware de JWT** — é público por design, protegido apenas por obscuridade da URL, como o próprio `routers/admin.py:1` documenta. O Apps Script depende disso (o `callBackend` do `Code.gs` não envia nenhum header de autorização).

Colocar os endpoints do console sob `/admin` significaria expor escrita de conteúdo sem autenticação. Movê-los para dentro do JWT quebraria o Apps Script. O prefixo novo `/console` resolve os dois: fica autenticado, e `/admin` segue intacto.

---

## Banco de Dados

**Nenhuma migration de schema.** A fatia A escreve em três tabelas existentes.

### `trip_phases`

Campos editáveis pelo console: `title`, `subtitle`, `icon`, `short_description`, `detailed_description`, `sort_order`, `is_visible`.

Campos fixados pelo console na criação: `wetravel_trip_uuid` (da viagem selecionada), `phase_type = 'pre-trip'`, `is_locked_by_default = false`, `is_visible = false`.

Campos não expostos nesta fatia: `parent_phase_id`, `starts_at`, `ends_at`.

### `trip_phase_checklist_items`

Campos editáveis: `label`, `is_required`, `sort_order`.

### `trip_phase_links`

Campos editáveis: `label`, `url`, `sort_order`.

### Rascunho e publicação

`is_visible` é a flag de publicação. Ela já é filtrada pelo app do viajante (`trip_service.py:142` e `:296`) e pelo staff (`routers/staff.py:264`), então uma fase em rascunho é invisível para ambos **sem nenhuma alteração de código nesses caminhos**.

| Estado | `is_visible` | Quem vê |
|---|---|---|
| Rascunho | `false` | Só o console |
| Publicada | `true` | Viajante e staff |

Fase nova nasce em rascunho. Publicar liga a flag; despublicar desliga. Editar uma fase publicada altera o que o viajante vê imediatamente — para editar sem expor, despublique antes. Essa limitação é aceita conscientemente: o caso que motivou a publicação em duas etapas é montar uma viagem do zero, e esse caso fica coberto.

### Identificadores

O import por planilha deriva o id da fase de forma determinística (`deterministic_phase_id(trip_uuid, phase_type, fase)`), a partir de um slug `fase` que **não é armazenado** em `trip_phases` — a coluna não existe. Fases criadas pelo console usam `uuid4()`.

A consequência é que os dois caminhos não se reconciliam: o import não "atualiza" uma fase criada no console, ele apaga tudo e recria. Isso é coerente com a decisão de que a planilha vira leitura, e está registrado como risco operacional abaixo.

---

## API — `/console`

Todos os endpoints exigem JWT válido **e** `role = 'admin'`. Sem token → `401`. Token de `traveler` ou `staff` → `403`.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/console/trips` | Lista viagens ativas |
| `GET` | `/console/trips/{uuid}/phases` | Árvore: fases pré-trip + checklist + links |
| `POST` | `/console/trips/{uuid}/phases` | Cria fase (nasce `is_visible=false`) |
| `PATCH` | `/console/phases/{id}` | Edita campos da fase |
| `DELETE` | `/console/phases/{id}` | Remove fase e seus filhos |
| `POST` | `/console/phases/{id}/publish` | `is_visible = true` |
| `POST` | `/console/phases/{id}/unpublish` | `is_visible = false` |
| `PUT` | `/console/phases/{id}/checklist` | Substitui a lista inteira, na ordem enviada |
| `PUT` | `/console/phases/{id}/links` | Substitui a lista inteira, na ordem enviada |
| `PUT` | `/console/trips/{uuid}/phases/order` | Reordena fases (lista de ids) |

`GET /console/trips` reusa a consulta de `admin_list_trips`, extraída para uma função compartilhada — sem duplicar SQL e sem alterar o endpoint `/admin/trips`.

### Por que `PUT` de lista inteira em checklist e links

A tela é uma lista arrastável e reordenar é a operação mais comum. Um `PUT` da lista inteira mantém `sort_order` sempre consistente e evita a sequência de chamadas parciais que deixaria a ordem quebrada se uma falhasse. As listas têm ordem de grandeza de dezenas de itens, então o custo de reenviar é irrelevante.

### Deleção de fase

`DELETE /console/phases/{id}` remove, em transação e nesta ordem: `traveler_checklist_progress` dos itens da fase, `traveler_phase_progress` da fase, `trip_phase_checklist_items`, `trip_phase_links`, e por fim a fase.

Fases `pre-trip` não recebem atividades pelo import, e hoje há **zero** registros em `trip_activities` ligados a uma fase `pre-trip` no banco de produção. Nada no schema impede esse vínculo, porém. O endpoint portanto verifica antes de deletar e, se encontrar atividades, recusa com `409` em vez de tentar apagar — evitando repetir a classe de erro de chave estrangeira que motivou este projeto.

---

## Frontend — `console/`

Projeto Vite + React + TypeScript, espelhando as escolhas do app atual (Tailwind, Vitest, Testing Library, MSW).

### Telas

1. **Login** — telefone e código OTP, contra `/auth`. Rejeita quem não é `admin` com mensagem clara.
2. **Viagens** — lista de viagens ativas. Contém o botão **Copiar link de pré-embarque**.
3. **Fases da viagem** — lista ordenável; cada linha mostra título, contagem de itens e o estado (rascunho/publicada), com ações de publicar, despublicar e excluir.
4. **Editor de fase** — campos da fase, mais as listas de checklist e links, ambas ordenáveis.

### Link de pré-embarque

```
https://parrot-trips.netlify.app/profile?section=pre-departure
```

Este link **já funciona em produção** e não requer nenhum desenvolvimento no app do viajante:

- `netlify.toml` já faz o fallback de SPA (`/*` → `/index.html`, status 200), então a URL responde `200`.
- `ProfileScreen.tsx:290` (`getLinkedProfileSection`) lê `?section=` e `:990` expande a seção `pre-departure` via `defaultOpen`.
- Nenhum código navega após o login (`LoginScreen.tsx` não chama `navigate`), então a URL sobrevive ao OTP e o `BrowserRouter` monta direto no destino.

O console apenas copia a string para a área de transferência.

**Pré-requisito:** o link só abre para telefone já cadastrado em `users` — `auth_service.py:109` responde `403 "Phone number not authorized"` caso contrário. Cadastro de viajantes permanece em aberto com os stakeholders e está fora desta fatia.

---

## Testes

**Backend** — pytest sobre o Postgres real já provido por `tests/conftest.py` (fixture `database_url`, que roda as migrations). Por endpoint: caminho feliz, validação de entrada, e autorização (sem token → `401`; `role=staff` → `403`). Mais dois testes de comportamento:

- fase criada nasce invisível e **não** aparece na resposta do app do viajante;
- publicar a fase faz ela aparecer.

**Frontend** — Vitest e Testing Library nos formulários, na lógica de reordenação e no guard de papel; MSW para as chamadas de API.

Todo o desenvolvimento segue TDD: teste falhando primeiro, verificado falhando pelo motivo certo, antes da implementação.

---

## Riscos e pontos abertos

1. **O import por planilha apaga o que o console criou.** `write_to_db` deleta todas as fases da viagem antes de reinserir. Decorre diretamente da decisão de não alterar as planilhas e não tem solução sem tocá-las. Mitigação sem alterar nada: a tela de fases exibe a data da última importação por planilha, para tornar o risco visível.
2. **Promoção do primeiro admin.** Será feita uma vez, direto no banco (`UPDATE users SET role='admin' WHERE phone=...`). Tela de gestão de usuários fica fora de escopo; `POST /admin/users/set-role` existe, mas está no prefixo público e não será usado pelo console.
3. **Cadastro de viajantes.** Segue pendente com os stakeholders; limita o alcance do link de pré-embarque.
4. **Admin abrindo o app do viajante.** O app do viajante decide a tela por `role` e só reconhece `traveler | staff` (`frontend/src/app/providers/auth-context.ts:3`). Um usuário `admin` que abrir o app cairá no fluxo de viajante e, se não estiver em `trip_travelers`, verá uma tela sem dados. Não quebra nada e não afeta viajantes reais, mas convém usar contas separadas para administrar e para testar o app. Tratar isso exigiria alterar o app do viajante, o que está fora de escopo.

---

## Fora de escopo

- Fatia B (Roteiro: dias e atividades)
- Fatia C (Informações: FAQ, política de cancelamento, contatos de emergência, recomendações)
- Fatia D (Staff: equipe, tarefas, participantes de atividades)
- Criação e edição de viagens
- Tela de gestão de usuários e papéis
- Histórico de alterações e auditoria de edições
- Upload de imagens
- Qualquer alteração no app do viajante, no Apps Script ou nos endpoints `/admin`
