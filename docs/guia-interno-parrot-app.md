# Guia interno — Como funciona o app da Parrot Trips

Este documento é para membros da equipe Parrot que vão operar e preparar viagens no app. Não é necessário conhecimento técnico.

---

## O que é o app

O app da Parrot Trips tem dois lados:

- **Lado do viajante** — o que a pessoa que comprou a viagem vê e usa.
- **Lado do staff** — o que a equipe operacional vê e usa durante a viagem.

Cada pessoa entra com o próprio número de WhatsApp. O sistema identifica automaticamente se ela é viajante ou staff e mostra a tela certa.

---

## De onde vem cada informação

As informações que aparecem no app vêm de três lugares diferentes. É importante entender isso para saber onde mexer quando algo precisar ser atualizado.

### 1. WeTravel — o que o viajante comprou

Quando uma pessoa compra uma viagem na WeTravel, o sistema salva automaticamente:

- Nome do viajante
- E-mail do viajante
- Telefone do viajante
- Pacote comprado
- Valor pago
- Add-ons comprados
- Tipo de quarto

Essas informações aparecem no app em **My Profile → Products & Payment**. A equipe não precisa digitar nada — chegam sozinhas da WeTravel.

> 📌 **Onde adicionar print:** tela do app mostrando Products & Payment com Package Name, Amount Paid e Add-on Activities preenchidos.

---

### 2. Planilhas — o conteúdo da viagem

Tudo que é conteúdo operacional da viagem vem das planilhas. A equipe preenche e exporta para o app com um clique.

Existem duas planilhas:

- **Planilha de Conteúdo** — conteúdo que o viajante vê (roteiro, fases, checklist, links)
- **Planilha de Staff** — conteúdo operacional (contatos, tarefas do staff, acessos)

---

### 3. O próprio viajante — dados pessoais

Alguns dados só o viajante pode preencher, diretamente no app em **My Profile → Registration Details**:

- Nome preferido
- Data de nascimento
- Gênero
- Informações de passaporte
- Restrições alimentares
- Enjoo
- Acompanhante (plus one)
- Pedido de ajuda com voos
- Pedido de ajuda com seguro viagem
- O que tornaria a viagem inesquecível

A equipe não precisa coletar essas informações manualmente.

---

## Como preparar uma viagem no app

### Passo 1 — A viagem existe na WeTravel

A viagem precisa estar criada na WeTravel com:

- Nome da viagem
- Data de início e fim
- Pacote comprável
- Add-ons (se houver)

Quando um viajante compra, o sistema recebe as informações automaticamente.

---

### Passo 2 — Preencher a Planilha de Conteúdo

A Planilha de Conteúdo tem as seguintes abas:

#### Aba Viagens

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código único da viagem (ex: `GSB-NYE-2026`) — não pode ter espaço |
| `nome_da_viagem` | Nome legível da viagem |
| `data_inicio` | Data de início no formato AAAA-MM-DD |
| `data_fim` | Data de fim no formato AAAA-MM-DD |
| `service_agreement_url` | Caminho do PDF do contrato (a equipe técnica fornece) |

> 📌 **Onde adicionar print:** aba Viagens preenchida com uma viagem de exemplo.

---

#### Aba Fases

Fases são as etapas do pré-trip que o viajante percorre antes de embarcar. Exemplos: Documentos, Packing, Voos.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Mesmo código da aba Viagens |
| `ordem` | Número que define a ordem de exibição (1, 2, 3...) |
| `fase` | Nome interno da fase — usado para linkar checklist e links |
| `titulo` | Título que o viajante vê |
| `subtitulo` | Subtítulo opcional |
| `icone` | Emoji ou ícone |
| `descricao_curta` | Texto curto que aparece no card |
| `descricao_completa` | Texto detalhado dentro da fase |
| `ideal_pace` | Marque `x` na fase em que os viajantes deveriam estar agora |

> 📌 **Onde adicionar print:** app mostrando as fases na tela Home do viajante.

---

#### Aba Checklist

Cada fase pode ter uma lista de tarefas que o viajante marca como feito.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código da viagem |
| `fase` | Nome da fase (igual ao campo `fase` na aba Fases) |
| `ordem` | Ordem da tarefa dentro da fase |
| `label` | Texto da tarefa que o viajante vê |
| `obrigatorio` | `sim` ou `não` |

> 📌 **Onde adicionar print:** app mostrando checklist dentro de uma fase.

---

#### Aba Links

Cada fase pode ter links úteis para o viajante.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código da viagem |
| `fase` | Nome da fase |
| `ordem` | Ordem do link |
| `label` | Texto do link que o viajante vê |
| `url` | Endereço completo do link |

---

#### Aba Roteiro

O roteiro é o itinerário in-trip — o que o viajante vê durante a viagem.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código da viagem |
| `dia` | Número do dia (1, 2, 3...) |
| `data` | Data no formato AAAA-MM-DD |
| `titulo` | Título do dia |
| `subtitulo` | Subtítulo do dia |
| `icone` | Emoji ou ícone |
| `descricao_curta` | Resumo do dia |
| `descricao_completa` | Texto completo do dia |
| `atividade` | Nome da atividade dentro do dia |
| `tipo` | Tipo da atividade: `included`, `optional`, `logistics`, `suggested` |
| `horario` | Horário no formato HH:MM (ex: `08:00`) |
| `duracao_min` | Duração em minutos (ex: `120` para 2 horas) |
| `descricao_atividade` | Descrição da atividade para o viajante |
| `info_pratica` | Informações práticas (o que levar, onde se encontrar, etc.) |
| `valor_brl` | Preço em reais, se for atividade opcional paga |

> 📌 **Onde adicionar print:** app mostrando um dia do roteiro com atividades e horários.

---

### Passo 3 — Exportar o conteúdo para o app

Depois de preencher a planilha, abra o menu **🦜 Parrot Trips** no topo da planilha e clique em:

**🚀 Export Trip Content to App**

O sistema vai perguntar qual viagem exportar. Escolha pelo `trip_uuid` e confirme. Em segundos o app já reflete o conteúdo atualizado.

> 📌 **Onde adicionar print:** menu Parrot Trips aberto mostrando os botões.

---

### Passo 4 — Preencher a Planilha de Staff

A Planilha de Staff tem suas próprias abas:

#### Aba Staff

Define quem faz parte da equipe operacional de uma viagem. Se a pessoa ainda não tem conta no app, ela é criada automaticamente ao exportar.

| Coluna | O que preencher |
|---|---|
| `phone` | Telefone com código do país (ex: `+5511999999999`) |
| `nome` | Nome completo |
| `funcao` | Função na viagem (ex: Guia, Coordenador) |
| `trip_uuid` | Código da viagem |

---

#### Aba Contatos

Contatos operacionais que aparecem para o staff no app durante a viagem.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código da viagem |
| `category` | Categoria (ex: Hotel, Transporte, Guia Local, Emergência) |
| `name` | Nome do contato |
| `role` | Função do contato |
| `phone` | Telefone |
| `sort_order` | Ordem de exibição |

---

#### Aba Tarefas Staff

Define quais tarefas cada membro do staff deve fazer em cada atividade. Cada pessoa vê apenas as próprias tarefas.

| Coluna | O que preencher |
|---|---|
| `trip_uuid` | Código da viagem |
| `dia` | Número do dia |
| `atividade_nome` | Nome da atividade (igual ao que está no Roteiro) |
| `staff_phone` | Telefone do staff responsável |
| `titulo` | Título da tarefa |
| `descricao` | Descrição da tarefa |
| `sort_order` | Ordem de exibição |

> 📌 **Onde adicionar print:** app do staff mostrando My Tasks dentro de uma atividade.

---

### Passo 5 — Exportar o conteúdo do staff

No menu **🦜 Parrot Staff** da planilha de staff, os botões disponíveis são:

| Botão | O que faz |
|---|---|
| 🔄 Sync Trips from App | Atualiza a lista de viagens disponíveis na planilha |
| Import Staff → Supabase | Cria/atualiza os membros do staff e os vincula à viagem |
| Import Contacts → Supabase | Envia os contatos operacionais para o app |
| Import Staff Tasks → Supabase | Envia as tarefas do staff para o app |

---

### Passo 6 — Iniciar a viagem

Quando a viagem começa e o app deve mudar do modo pré-trip para o roteiro in-trip, abra o menu **🦜 Parrot Trips** e clique em:

**▶️ Start Trip**

A partir desse momento o viajante vê o itinerário do dia no lugar das fases de preparação.

---

## O que o viajante vê no app

### Home — Pré-trip

Antes da viagem começar, o viajante vê as fases de preparação com checklist e links. O progresso é salvo automaticamente.

### Home — In-trip

Durante a viagem, o viajante vê o itinerário do dia com as atividades, horários e informações práticas.

### My Profile

Dividido em três seções:

**Registration Details** — preenchido pelo próprio viajante. Dados pessoais, passaporte, saúde, acompanhante.

**Products & Payment** — preenchido automaticamente pela WeTravel. Pacote, valor pago, add-ons e tipo de quarto.

**Service Agreement** — documento do contrato da viagem. Configurado pela equipe na planilha. O viajante pode consultar a qualquer momento.

### QR Code

O viajante tem um QR Code próprio que o staff escaneia para registrar presença nas atividades.

> 📌 **Onde adicionar print:** tela do QR Code no app do viajante.

---

## O que o staff vê no app

- **Itinerário** — os dias e atividades da viagem.
- **My Tasks** — dentro de cada atividade, o staff vê apenas as próprias tarefas.
- **Scan Traveler** — câmera para escanear o QR Code do viajante e registrar presença.
- **Contacts** — lista de contatos operacionais da viagem.
- **Traveler view** — botão para alternar temporariamente para a visão do viajante.

> 📌 **Onde adicionar print:** app do staff mostrando o itinerário e o botão Scan Traveler.

---

## Outros botões do menu Parrot Trips

| Botão | Quando usar |
|---|---|
| 🔄 Sync Trips from App | Para atualizar a lista de viagens na aba Viagens antes de exportar |
| 🔁 Reset Trip to Pre-Trip | Para voltar a viagem ao modo pré-trip durante testes |
| 🗑️ Clear Trip Content | Para apagar todo o conteúdo de uma viagem e reimportar do zero |
| 🔧 Setup Sheet Headers | Apenas na primeira vez que usar a planilha — cria as abas com os cabeçalhos certos |

---

## Resumo — quem alimenta o quê

| Informação | Quem alimenta |
|---|---|
| Pacote, valor, add-ons, tipo de quarto | WeTravel — automático na compra |
| Nome e e-mail base do viajante | WeTravel — automático na compra |
| Dados pessoais e passaporte | O próprio viajante no app |
| Fases, checklist e links do pré-trip | Equipe Parrot — Planilha de Conteúdo |
| Roteiro e atividades | Equipe Parrot — Planilha de Conteúdo |
| Contrato (Service Agreement) | Equipe Parrot — Planilha de Conteúdo |
| Staff e funções | Equipe Parrot — Planilha de Staff |
| Contatos operacionais | Equipe Parrot — Planilha de Staff |
| Tarefas do staff por atividade | Equipe Parrot — Planilha de Staff |
