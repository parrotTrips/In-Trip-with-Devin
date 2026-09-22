# Plataforma de Conteúdo (Console) — acompanhamento

Documento de validação. Resume o que estamos construindo, por quê, e como conferir cada etapa.

- **Design completo:** `docs/superpowers/specs/2026-09-21-content-console-design.md`
- **Plano do backend:** `docs/superpowers/plans/2026-09-21-content-console-backend.md`
- **Plano do console (frontend):** `docs/superpowers/plans/2026-09-21-content-console-frontend.md`

---

## Por que estamos fazendo isso

Digitar conteúdo em planilha vinha falhando por motivos estruturais, não por descuido:

| Problema | O que acontecia |
|---|---|
| Sem campo obrigatório | Linha com `trip_uuid` em branco era descartada em silêncio, e o import respondia "No data found" |
| Sem integridade | `fase` digitada no Checklist que não existe em Fases some sem aviso |
| Import destrutivo | Cada importação apaga e recria tudo, destruindo check-ins e scans junto |
| Sem rastro | Ninguém sabe quem mudou o quê |

A plataforma resolve os quatro: campo obrigatório no formulário, referência escolhida em lista, **edição incremental** (o registro é atualizado, não recriado) e usuário identificado por login.

---

## Decisões tomadas

| Tema | Decisão |
|---|---|
| Planilhas | **Continuam exatamente como estão.** Nada é removido nem alterado. Na prática viram leitura |
| Primeira fatia | Fases + Checklist + Links (o "jogo da vida" pré-trip) |
| Onde vive | App novo e separado, com deploy próprio. O app do viajante não muda |
| Publicação | Rascunho + publicar, tendo a **fase** como unidade |
| Acesso | Google Workspace; qualquer conta válida `@parrottrips.com` tem acesso completo |
| Link de pré-embarque | Botão de copiar — o link já funciona hoje |
| Criar viagens | Fora de escopo: viagens continuam vindo do WeTravel |

---

## Objetivo: paridade total com as planilhas

A plataforma tem que fazer **tudo** o que as duas planilhas fazem hoje. O inventário
completo está abaixo — é por ele que se mede se chegamos lá.

### Fatias

| Fatia | Cobre | Abas / ações de origem | Status |
|---|---|---|---|
| **A** | Jogo da vida (pré-trip) | Fases, Checklist, Links | **Concluída** |
| **B** | Roteiro | Roteiro (dias e atividades) | Não iniciada |
| **C** | Informações | Emergency Contacts, Recomendacoes, FAQ, Cancellation Policy | Não iniciada |
| **D** | Staff | Staff, Contatos, Tarefas Staff, Participantes Atividades | Não iniciada |
| **E** | Operação | Start Trip, Reset Trip, Clear Content, ver Feedbacks | Não iniciada |

### O que não migra

Três ações existem só para manter a planilha viva e deixam de fazer sentido:

| Ação | Por quê |
|---|---|
| 🔧 Setup Sheet Headers | Cria as abas da planilha |
| ⬇️ Import Trips from App | Copia viagens para a aba; na plataforma o dado já vem do banco |
| sync-to-sheet / write-staff-bios | Devolvem `address`, `max_checkins` e bios **para** a planilha |

Pendente de confirmação: a aba **Viajantes Teste** da planilha de conteúdo não aparece
em nenhum menu — precisa ser migrada ou pode ser descartada?

---

## Progresso da fatia A

### Backend

| # | Entrega | Como validar | Status |
|---|---|---|---|
| 1 | API autenticada e lista de viagens | Sem ID token válido não entra; domínio externo é recusado | ✅ |
| 2 | Ler fases com checklist e links | A tela consegue carregar o conteúdo de uma viagem | ✅ |
| 3 | Criar fase (nasce em rascunho) | Fase nova **não** aparece no app do viajante | ✅ |
| 4 | Editar, publicar e despublicar | Publicou, apareceu; despublicou, sumiu | ✅ |
| 5 | Excluir fase | Exclui fase e filhos, e recusa se houver atividade vinculada | ✅ |
| 6 | Editar checklist e links | Salva a lista na ordem em que está na tela | ✅ |
| 7 | Reordenar fases | A ordem da tela é a ordem que o viajante vê | ✅ |

### Console (interface)

| # | Entrega | Como validar | Status |
|---|---|---|---|
| 1 | Projeto `console/` | `npm run build` e `npm run test` rodam | ✅ |
| 2 | Login Google Workspace | Qualquer conta válida `@parrottrips.com` entra; domínio externo é recusado | ✅ |
| 3 | Tela de viagens | Lista as viagens; botão copia o link de pré-embarque | ✅ |
| 4 | Tela de fases | Mostra Rascunho/Publicada; criar, publicar, excluir | ✅ |
| 5 | Editor de fase | Campos, checklist e links; salva na ordem da tela | ✅ |
| 6 | Reordenar fases | Botão Subir grava a nova ordem | ✅ |
| 7 | Deploy | `netlify.toml` e `make console-deploy` | ✅ |

**Fatia A concluída de ponta a ponta.**

O console agora usa ID token Google stateless e não consulta `users.role` nem mantém banco de
usuários próprio. Backend: a suíte de endurecimento passa. Console: **38 testes**, build limpo.
A única falha histórica
(`test_activity_checkins_table_metadata`) é anterior a este trabalho — a migration `0016`
mudou a chave única de `activity_checkins` e o teste não foi atualizado junto.

### Para colocar no ar

1. Configurar o OAuth Web Client do Google e as variáveis descritas no `README.md`
2. `make deploy-backend` — a API `/console` e o fix dos scan events ainda não estão publicados
3. Fazer smoke tests sem mutação: `/health`, 401 sem token e login corporativo
4. Criar o site Netlify do console e rodar `make console-deploy CONSOLE_NETLIFY_SITE=<site-id>`

Próximo: fatias B, C, D e E, até a paridade total.

---

## Como o rascunho funciona

Cada fase tem um estado:

| Estado | Quem vê |
|---|---|
| **Rascunho** | Só você, na plataforma |
| **Publicada** | Viajante e staff |

Fase nova nasce em rascunho — dá para montar a viagem inteira sem ninguém ver nada pela metade. Publicar libera.

Fases publicadas são somente leitura no backend e na interface. Para editar, despublique antes,
faça a alteração e publique novamente.

---

## Link de pré-embarque

```
https://parrot-trips.netlify.app/profile?section=pre-departure
```

Quem abrir esse link cai direto na seção **Pre Departure Information**, já aberta. Se não estiver logado, faz o login por WhatsApp e continua para lá — o endereço não se perde no caminho.

**Já funciona hoje**, sem nenhum desenvolvimento no app do viajante. A plataforma só vai oferecer o botão de copiar.

⚠️ **Só abre para quem já tem telefone cadastrado.** Quem não estiver cadastrado recebe "Phone number not authorized" no login. O cadastro de viajantes continua em aberto com os stakeholders e não faz parte desta fatia.

---

## Pontos de atenção

1. **Não clique em "Export Trip Content to App" depois de editar na plataforma.** O import apaga as fases da viagem e recria — leva junto o que foi feito na plataforma. Isso decorre da decisão de não mexer nas planilhas. A interface mostra um aviso persistente sobre esse risco.
2. O console não usa allowlist ou papel `admin`: toda conta Google Workspace válida
   `@parrottrips.com` recebe acesso completo.
3. O login Google do console é independente do login por WhatsApp usado no app do viajante.

---

## Fora de escopo da fatia A

Fatias B, C, D e E (ver o mapa de paridade acima), criação de viagens, tela de usuários,
histórico de alterações, upload de imagens, e qualquer alteração no app do viajante, no
Apps Script ou nos endpoints `/admin`.
