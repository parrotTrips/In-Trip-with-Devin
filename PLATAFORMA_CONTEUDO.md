# Plataforma de Conteúdo (Console) — acompanhamento

Documento de validação. Resume o que estamos construindo, por quê, e como conferir cada etapa.

- **Design completo:** `docs/superpowers/specs/2026-09-21-content-console-design.md`
- **Plano do backend:** `docs/superpowers/plans/2026-09-21-content-console-backend.md`
- **Plano do console (frontend):** a escrever, depois que o backend estiver pronto

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
| Acesso | Papel `admin`, login por WhatsApp OTP (o mesmo de sempre) |
| Link de pré-embarque | Botão de copiar — o link já funciona hoje |
| Criar viagens | Fora de escopo: viagens continuam vindo do WeTravel |

---

## Fatias

| Fatia | Conteúdo | Status |
|---|---|---|
| **A** | Fases, Checklist, Links | Em andamento |
| B | Roteiro (dias e atividades) | Não iniciada |
| C | Informações (FAQ, política, contatos, recomendações) | Não iniciada |
| D | Staff (equipe, tarefas, participantes) | Não iniciada |

---

## Progresso da fatia A — backend

| # | Entrega | Como validar | Status |
|---|---|---|---|
| 1 | API autenticada e lista de viagens | Sem login não entra; quem não é admin recebe "acesso negado" | ⬜ |
| 2 | Ler fases com checklist e links | A tela consegue carregar o conteúdo de uma viagem | ⬜ |
| 3 | Criar fase (nasce em rascunho) | Fase nova **não** aparece no app do viajante | ⬜ |
| 4 | Editar, publicar e despublicar | Publicou, apareceu; despublicou, sumiu | ⬜ |
| 5 | Excluir fase | Exclui fase e filhos, e recusa se houver atividade vinculada | ⬜ |
| 6 | Editar checklist e links | Salva a lista na ordem em que está na tela | ⬜ |
| 7 | Reordenar fases | A ordem da tela é a ordem que o viajante vê | ⬜ |

*(Atualizo esta tabela conforme cada etapa fica pronta e testada.)*

---

## Como o rascunho funciona

Cada fase tem um estado:

| Estado | Quem vê |
|---|---|
| **Rascunho** | Só você, na plataforma |
| **Publicada** | Viajante e staff |

Fase nova nasce em rascunho — dá para montar a viagem inteira sem ninguém ver nada pela metade. Publicar libera.

**Limitação aceita:** editar uma fase **já publicada** vale na hora para o viajante. Para mexer escondido, despublique antes, edite e publique de novo.

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

1. **Não clique em "Export Trip Content to App" depois de editar na plataforma.** O import apaga as fases da viagem e recria — leva junto o que foi feito na plataforma. Isso decorre da decisão de não mexer nas planilhas. A tela vai mostrar a data da última importação para deixar o risco visível.
2. **O primeiro admin é promovido direto no banco**, uma vez. Não haverá tela de gestão de usuários nesta fatia.
3. **Use contas separadas** para administrar e para testar o app do viajante. Um usuário `admin` que abrir o app do viajante cai no fluxo de viajante e vê tela sem dados, porque o app só conhece os papéis `traveler` e `staff`.

---

## Fora de escopo nesta fatia

Roteiro, Informações, Staff, criação de viagens, tela de usuários, histórico de alterações, upload de imagens, e qualquer alteração no app do viajante, no Apps Script ou nos endpoints `/admin`.
