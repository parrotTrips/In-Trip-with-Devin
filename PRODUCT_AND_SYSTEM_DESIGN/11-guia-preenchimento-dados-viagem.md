# Guia de Preenchimento de Dados das Viagens

> Documento para o time Parrot Trips preencher o conteúdo de cada viagem no app.

---

## Contexto

O app exibe duas categorias de conteúdo por viagem:

1. **Fases pré-viagem** — checklist de preparação (visto, vacinas, mala, documentos)
2. **Roteiro dia a dia** — atividades de cada dia com horário, tipo e descrição

O conteúdo abaixo precisa ser preenchido **uma vez por viagem**. Após preenchido, fica disponível para todos os viajantes daquela viagem no app.

---

## Parte 1 — Fases Pré-Viagem

São 4 fases fixas em todas as viagens. Para cada fase, preencher:

---

### Fase 1: Visto

**Texto explicativo** (2–4 parágrafos, aparece ao abrir a fase):
> O que o viajante precisa saber sobre o visto para este destino? Requisitos por nacionalidade, prazo de solicitação, onde solicitar, o que levar na entrada.

**Checklist** (lista de itens que o viajante deve marcar como feito):
> Ex: "Verificar se sua nacionalidade precisa de visto", "Solicitar eVisa no portal oficial", "Salvar comprovante de aprovação"

**Links úteis** (nome do link + URL):
> Ex: "Portal eVisa Brasil", "Informações para cidadãos americanos"

---

### Fase 2: Vacinas

**Texto explicativo:**
> Vacinas obrigatórias ou recomendadas para o destino. Febre amarela, COVID, Hepatite A/B, etc. Certificado internacional necessário?

**Checklist:**
> Ex: "Tomar vacina de febre amarela", "Obter carteira de vacinação internacional", "Guardar carteira de vacinação na bagagem de mão"

**Links úteis:**
> Ex: "CDC — recomendações para o Brasil", "OMS — vacinação para viajantes"

---

### Fase 3: Mala

**Texto explicativo:**
> Clima do destino, dicas de bagagem, o que é essencial, o que evitar levar. Tipo de tomada, conversor necessário?

**Checklist:**
> Ex: "Roupas leves e respiráveis", "Protetor solar FPS 50+", "Adaptador de tomada", "Mochila pequena para passeios"

**Links úteis:**
> Ex: "Previsão do tempo para o destino", "Guia de tomadas do país"

---

### Fase 4: Documentos

**Texto explicativo:**
> Quais documentos levar, onde guardar cópias, o que a Parrot Trips fornece vs. o que é responsabilidade do viajante.

**Checklist:**
> Ex: "Passaporte válido (6+ meses)", "Comprovante de visto impresso", "Seguro viagem", "Formulário de pré-viagem enviado para a Parrot Trips"

**Links úteis:**
> Ex: "Baixar formulário de pré-viagem", "Guia de seguro viagem"

---

## Parte 2 — Roteiro Dia a Dia

Para cada dia da viagem, preencher:

### Cabeçalho do dia

| campo | exemplo | descrição |
|---|---|---|
| Data | 8 de dezembro | Data exata do dia |
| Título | `Day 1 — Dec 8` | Nome curto do dia (aparece na lista) |
| Subtítulo | `Chegada ao Rio` | Resumo de uma linha do dia |
| Ícone | `plane-landing` | Ver lista de ícones disponíveis abaixo |
| Descrição curta | `Transfer do aeroporto, check-in no hotel e Welcome Happy Hour` | Aparece no card da HomeScreen |
| Descrição completa | Texto maior com mais contexto do dia | Aparece ao abrir o dia |

**Ícones disponíveis:** `plane-landing`, `plane`, `sun`, `mountain`, `ship`, `sailboat`, `palmtree`, `bus`, `flame`, `landmark`, `luggage`

---

### Atividades do dia

Para cada atividade, preencher:

| campo | obrigatório | exemplo | descrição |
|---|---|---|---|
| Nome | ✅ | `Transfer do Aeroporto` | Nome curto que aparece no card |
| Tipo | ✅ | `inclusa` | Ver tipos abaixo |
| Horário | — | `10:00` | Horário de início (deixar em branco se não tiver) |
| Duração | — | `120` | Em minutos (deixar em branco se não tiver) |
| Descrição curta | ✅ | `Transfer do aeroporto para o hotel conforme informado no formulário de pré-viagem` | Texto principal do card |
| Informações práticas | — | `Ponto de encontro: área de desembarque, Portão A. Levar documento com foto.` | Dicas extras, ponto de encontro, dress code, o que levar |
| Preço em R$ | só para opcionais | `150` | Apenas para atividades do tipo **opcional** |

**Tipos de atividade:**

| tipo | quando usar |
|---|---|
| `inclusa` | Atividade paga pela Parrot Trips, todos participam |
| `opcional` | Atividade extra com custo adicional, o viajante escolhe se quer |
| `sugestão` | Recomendação da Parrot Trips para o tempo livre |
| `logística` | Transfer, check-in/check-out, informação operacional |

---

## Exemplo preenchido — Dia 1

**Cabeçalho:**
- Data: 8 de dezembro
- Título: `Day 1 — Dec 8`
- Subtítulo: `Chegada ao Rio`
- Ícone: `plane-landing`
- Descrição curta: `Transfer do aeroporto, check-in no hotel e Welcome Happy Hour`
- Descrição completa: `Bem-vindos ao Rio de Janeiro! Você será recebido no aeroporto e levado ao hotel. Após o check-in, aproveite a tarde na Praia de Ipanema e junte-se a todos no Welcome Happy Hour.`

**Atividades:**

| Nome | Tipo | Horário | Duração | Descrição curta | Informações práticas | Preço |
|---|---|---|---|---|---|---|
| Transfer do Aeroporto | logística | — | — | Recepção no aeroporto conforme formulário de pré-viagem | Procurar placa com o nome da Parrot Trips na área de desembarque | — |
| Check-in Hotel | logística | 14:00 | — | Check-in a partir das 14h. Guarda-volumes disponível para chegadas antecipadas | — | — |
| Praia de Ipanema | sugestão | 15:00 | 120 | Aproveite a praia a dois quarteirões do hotel | Leve protetor solar e documentos no hotel | — |
| Welcome Happy Hour | inclusa | 17:00 | 240 | Open bar na praia! Caipirinha, cerveja, petiscos brasileiros. Conheça o time Parrot! | Local: La Carioca En La Playa. Casual. | — |
| City Tour Panorâmico | opcional | 09:00 | 180 | Passeio de van pelos principais pontos turísticos do Rio | Saída do lobby do hotel | R$ 120 |

---

## Como entregar

Todo o conteúdo de todas as viagens fica em **uma única planilha**: [Parrot Trips — Conteúdo de Viagens](https://drive.google.com/drive/folders/1mqUSDMygVJ-rAFlHQJEyRjTpDPx9MilP).

A planilha tem duas abas:

- **Pre-Trip** — preencher as 4 fases (Visto, Vacinas, Mala, Documentos) para cada viagem. Cada linha começa com o `trip_uuid` da viagem.
- **Roteiro** — preencher uma linha por atividade para cada viagem. Cada linha começa com o `trip_uuid` da viagem.

Para encontrar o `trip_uuid` de cada viagem, ver a tabela abaixo.

Ao terminar o preenchimento, avise a equipe de desenvolvimento com o `trip_uuid` — o import para o banco leva menos de 5 minutos.

---

## Viagens e seus trip_uuid

| viagem | início | trip_uuid | status |
|---|---|---|---|
| K-LATAM 26 Brazil Trek | 20 Nov 2026 | a ver no banco | ⚠️ sem conteúdo |
| YSOM Brazil Trek 26 | 21 Nov 2026 | a ver no banco | ⚠️ sem conteúdo |
| Wharton Brazil Trek December 2026 | 8 Dec 2026 | a ver no banco | ⚠️ sem conteúdo |
| GSB NYE Brazil Trek | 26 Dec 2026 | a ver no banco | ⚠️ sem conteúdo |
| HBS Diaspora Brazil Trek | 15 Jan 2027 | a ver no banco | ⚠️ sem conteúdo |
| Wharton Carnaval Trek 2027 | 4 Feb 2027 | a ver no banco | ⚠️ sem conteúdo |
| UCLA Carnival 27 Trek | 5 Feb 2027 | a ver no banco | ⚠️ sem conteúdo |

**Prioridade sugerida:** começar pelas viagens com data mais próxima — K-LATAM e YSOM em novembro de 2026.
