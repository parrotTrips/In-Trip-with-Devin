# Console — Navegação por Seções da Viagem — Design

**Data:** 2026-09-22
**Status:** Aprovado

---

## Contexto

O console hoje mostra uma coisa só depois que a viagem é escolhida: Fases. Mas uma viagem
tem treze seções, e as viagens reais estão quase vazias — a Wharton Brazil Trek tem 43
viajantes e nenhuma recomendação, FAQ ou contato de emergência. Sem enxergar o todo, não dá
para saber o que falta preencher.

Esta entrega dá ao console a **visão completa da viagem**: todas as seções presentes,
navegáveis, mostrando o que já existe. A edição chega depois, seção por seção.

Isso também expande o objetivo do projeto. Até aqui o console mirava paridade com as
planilhas; **Viajantes e Feedbacks não vêm de planilha nenhuma** — vêm do WeTravel e do
próprio app. O console passa a ser a visão da viagem, não só o substituto da planilha.

---

## Decisões

| Tema | Decisão |
|---|---|
| Primeira entrega | Esqueleto navegável: ver tudo, editar só Fases |
| Agrupamento | Por natureza do dado, em quatro grupos |
| Navegação | Barra lateral fixa, com contagem por seção |
| Backend | Um endpoint genérico com registro de seções, não treze rotas |
| Dados de viajante | Apenas nome, contato e status de preenchimento |

---

## As treze seções

| Grupo | Seções |
|---|---|
| **Conteúdo do app** | Fases pré-trip, Roteiro, Recomendações, FAQ, Política de cancelamento, Contatos de emergência |
| **Pessoas** | Viajantes, Staff, Contatos operacionais |
| **Durante a viagem** | Avisos, Tarefas de staff |
| **Retorno** | Feedbacks |

O agrupamento separa o que a Parrot escreve do que chega de fora. Abrir *Viajantes* esperando
cadastrar alguém e descobrir que o dado vem do WeTravel é o tipo de frustração que o
agrupamento evita.

---

## Backend

### Registro de seções

Doze seções de leitura são doze listas simples. Em vez de doze rotas quase idênticas, um
registro em `app/services/console_sections.py`:

```python
@dataclass(frozen=True)
class Section:
    label: str
    group: str
    sql: str        # devolve as linhas da seção
    count_sql: str  # devolve a contagem
    readonly_reason: str | None = None
```

Todas as consultas recebem o `trip_uuid` como parâmetro nomeado. **O nome da seção vem do
cliente e é validado contra as chaves do registro** — nada vindo de fora entra em SQL.

### Rotas

```
GET /console/trips/{uuid}/sections              → seções, grupos e contagens
GET /console/trips/{uuid}/sections/{section}    → linhas de uma seção
```

Seção desconhecida responde `404`. Ambas exigem `role=admin`, como o resto de `/console`.

`fases` aparece na listagem de `/sections` (para a contagem na barra lateral), mas **não** no
registro genérico: ela já tem rotas próprias e continua usando-as. Pedir
`/sections/fases` responde `404`, com a mensagem apontando a rota correta.

Quando uma seção ganhar edição, ela sai do registro e passa a ter rotas próprias, como Fases.

### Colunas por seção

| Seção | Colunas |
|---|---|
| Roteiro | dia, data, título, nº de atividades |
| Recomendações | nome, categoria, bairro, endereço |
| FAQ | pergunta, resposta |
| Política de cancelamento | título, corpo |
| Contatos de emergência | nome, função, telefone |
| Viajantes | nome, telefone, e-mail, perfil preenchido |
| Staff | nome, função, telefone |
| Contatos operacionais | categoria, nome, função, telefone |
| Avisos | título, corpo, enviado em |
| Tarefas de staff | título, fase, responsável |
| Feedbacks | viajante, texto, enviado em |

### Privacidade dos dados de viajante

`traveler_profiles` guarda passaporte (número, país, validade), data de nascimento, gênero,
restrições alimentares, resposta sobre enjoo e dados de seguro. **Nada disso é exposto.**

A seção Viajantes mostra nome, telefone, e-mail e um indicador booleano de perfil preenchido,
derivado da existência dos campos-chave do pré-embarque — nunca os valores em si. Quem precisa
conferir um passaporte usa o app do viajante, onde o dado pertence a quem o forneceu.

---

## Frontend

### Rotas

```
/trips/:tripUuid                 → redireciona para /fases
/trips/:tripUuid/fases           → o editor atual, inalterado
/trips/:tripUuid/:section        → seção de leitura
```

A barra lateral é um layout que envolve todas as rotas de viagem: nome da viagem, link de
volta, e os quatro grupos com suas seções e contagens.

### Tabela configurada

Um componente `SectionTable` recebe colunas e linhas. Cada seção de leitura é uma entrada de
configuração, não um componente novo.

Seções sem edição mostram uma faixa: *"Somente leitura por enquanto — a edição desta seção
ainda não foi construída."* Feedbacks leva uma faixa diferente, porque é leitura **por
natureza**: o conteúdo vem dos viajantes.

Seção vazia mostra um estado explícito de "nada cadastrado ainda", que é exatamente o sinal
útil ao abrir uma viagem nova.

---

## Testes

**Backend:** cada seção do registro é consultada contra um Postgres real e devolve apenas
linhas da viagem pedida; seção desconhecida responde `404`; `/sections` traz contagens
corretas; a seção Viajantes não devolve nenhum campo sensível. Mais os casos de autorização
que já valem para `/console`.

**Console:** a barra lateral renderiza os quatro grupos com contagens; navegar troca a seção;
tabela vazia mostra o estado próprio; a faixa de somente-leitura aparece onde deve e não
aparece em Fases.

---

## Fora de escopo

- Edição em qualquer seção nova
- Import e export de CSV
- As mudanças do plano de hardening (SSO, imutabilidade de publicadas) — independentes desta
  entrega e sem conflito, por tocarem outros arquivos
- Criação de viagens, busca, filtros e paginação: os volumes são de dezenas de linhas
