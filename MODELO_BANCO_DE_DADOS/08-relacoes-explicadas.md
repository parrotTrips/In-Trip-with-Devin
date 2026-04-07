# Relações Explicadas

Este documento explica as relações do modelo de forma simples e em alto nível.

O foco aqui é responder perguntas como:

- quem se relaciona com quem
- se a relação é `1:1`, `1:N` ou `N:N`
- o que isso significa na prática
- como isso aparece com exemplos fictícios

## `users` -> `trip_travelers`

Cardinalidade:

- `User 1 -> 0..N TripTraveler`

O que significa:

- um mesmo viajante pode participar de nenhuma, uma ou várias viagens
- cada participação em uma viagem gera um registro em `trip_travelers`

Exemplo:

- `users`
  - `U1 = Bernardo`
- `trip_travelers`
  - `TT1 = (U1, T1)`
  - `TT2 = (U1, T2)`

Leitura:

- Bernardo pode estar na viagem `T1`
- e também pode estar na viagem `T2`
- por isso um `user` pode gerar vários `trip_travelers`

## `trips` -> `trip_travelers`

Cardinalidade:

- `Trip 1 -> 0..N TripTraveler`

O que significa:

- uma viagem pode ter vários viajantes
- cada viajante dentro daquela viagem vira um registro em `trip_travelers`

Exemplo:

- `trips`
  - `T1 = Réveillon 2027`
- `trip_travelers`
  - `TT1 = (U1, T1)`
  - `TT2 = (U2, T1)`
  - `TT3 = (U3, T1)`

Leitura:

- a viagem `T1` tem vários participantes

## `trip_travelers` -> `traveler_profiles`

Cardinalidade:

- `TripTraveler 1 -> 0..1 TravelerProfile`

O que significa:

- cada vínculo "viajante dentro da viagem" pode ter no máximo um perfil
- esse perfil é específico daquela viagem

Exemplo:

- `trip_travelers`
  - `TT1 = (U1, T1)`
  - `TT2 = (U1, T2)`
- `traveler_profiles`
  - `P1 -> TT1`
  - `P2 -> TT2`

Leitura:

- o mesmo usuário pode ter perfis diferentes em viagens diferentes
- mas cada `trip_traveler` tem no máximo um `traveler_profile`

## `trip_travelers` -> `traveler_products`

Cardinalidade:

- `TripTraveler 1 -> 0..1 TravelerProduct`

O que significa:

- cada viajante na viagem pode ter um bloco de dados comerciais/operacionais
- esse bloco guarda pacote, quarto, valor pago e contrato

Exemplo:

- `trip_travelers`
  - `TT1 = (U1, T1)`
- `traveler_products`
  - `PR1 -> TT1`

Leitura:

- os dados de compra pertencem ao viajante naquela viagem específica

## `traveler_products` -> `media_assets`

Cardinalidade:

- `TravelerProduct 0..N -> 0..1 MediaAsset`

O que significa:

- vários registros de produto podem apontar para um mesmo ativo de mídia, se fizer sentido
- no caso mais comum, o `traveler_product` aponta para um arquivo de contrato

Exemplo:

- `media_assets`
  - `M1 = contrato.pdf`
- `traveler_products`
  - `PR1 -> M1`

Leitura:

- o contrato do viajante é um arquivo guardado em `media_assets`

## `trips` -> `trip_phases`

Cardinalidade:

- `Trip 1 -> 0..N TripPhase`

O que significa:

- uma viagem pode ter várias fases
- essas fases podem ser pré-viagem ou durante a viagem

Exemplo:

- `trips`
  - `T1 = Réveillon 2027`
- `trip_phases`
  - `PH1 = Visa`
  - `PH2 = Packing`
  - `PH3 = Day 1`

Leitura:

- todas essas fases pertencem à mesma viagem `T1`

## `trip_phases` -> `trip_phases` (pai e filha)

Cardinalidade:

- `TripPhase 0..N -> 0..1 TripPhase (parent)`

O que significa:

- uma fase pode ter uma fase pai
- isso permite hierarquia entre fases

Exemplo:

- `PH10 = Day 3`
- `PH11 = Morning`
- `PH12 = Evening`

Leitura:

- `PH11` e `PH12` podem apontar para `PH10` como fase pai

## `trip_phases` -> `trip_phase_checklist_items`

Cardinalidade:

- `TripPhase 1 -> 0..N TripPhaseChecklistItem`

O que significa:

- uma fase pode ter vários itens de checklist

Exemplo:

- `PH1 = Visa`
- `I1 = verificar necessidade de visto`
- `I2 = emitir eVisa`

Leitura:

- os itens `I1` e `I2` pertencem à fase `PH1`

## `trip_phases` -> `trip_phase_links`

Cardinalidade:

- `TripPhase 1 -> 0..N TripPhaseLink`

O que significa:

- uma fase pode ter vários links úteis

Exemplo:

- `PH1 = Visa`
- `L1 = Portal do eVisa`
- `L2 = Informações consulares`

Leitura:

- ambos os links pertencem à fase `PH1`

## `trip_phases` -> `trip_activities`

Cardinalidade:

- `TripPhase 1 -> 0..N TripActivity`

O que significa:

- uma fase do tipo dia pode ter várias atividades

Exemplo:

- `PH3 = Day 1`
- `A1 = Airport Pickup`
- `A2 = Welcome Happy Hour`

Leitura:

- as atividades `A1` e `A2` pertencem à fase `PH3`

## `trip_activities` -> `activity_media`

Cardinalidade:

- `TripActivity 1 -> 0..N ActivityMedia`

O que significa:

- uma atividade pode ter várias mídias

Exemplo:

- `A2 = Welcome Happy Hour`
- `AM1`
- `AM2`

Leitura:

- a atividade `A2` pode ter duas imagens ou uma imagem e um vídeo

## `activity_media` -> `media_assets`

Cardinalidade:

- `ActivityMedia N -> 1 MediaAsset`
- `MediaAsset 1 -> 0..N ActivityMedia`

O que significa:

- `activity_media` é a ligação entre a atividade e o arquivo real
- o arquivo em si fica em `media_assets`

Exemplo:

- `activity_media`
  - `AM1 -> M10`
- `media_assets`
  - `M10 = happy-hour-1.jpg`

Leitura:

- a mídia da atividade aponta para um arquivo específico

## `trip_travelers` -> `traveler_checklist_progress`

Cardinalidade:

- `TripTraveler 1 -> 0..N TravelerChecklistProgress`

O que significa:

- um viajante dentro de uma viagem pode ter vários registros de progresso de checklist
- normalmente um por item de checklist

Exemplo:

- `trip_travelers`
  - `TT1 = (U1, T1)`
- `traveler_checklist_progress`
  - `CP1 = TT1 + I1`
  - `CP2 = TT1 + I2`

Leitura:

- o viajante `TT1` tem um estado próprio para cada item da fase

## `trip_phase_checklist_items` -> `traveler_checklist_progress`

Cardinalidade:

- `TripPhaseChecklistItem 1 -> 0..N TravelerChecklistProgress`

O que significa:

- o mesmo item de checklist pode ter progresso para vários viajantes

Exemplo:

- `I1 = emitir eVisa`
- `CP1 = TT1 + I1`
- `CP2 = TT2 + I1`

Leitura:

- o item é o mesmo
- o estado muda por viajante

## `trip_travelers` -> `traveler_phase_progress`

Cardinalidade:

- `TripTraveler 1 -> 0..N TravelerPhaseProgress`

O que significa:

- um viajante pode ter progresso em várias fases da viagem

Exemplo:

- `TT1 = (U1, T1)`
- `PP1 = TT1 + PH1`
- `PP2 = TT1 + PH2`

Leitura:

- o mesmo viajante tem um estado separado para cada fase

## `trip_phases` -> `traveler_phase_progress`

Cardinalidade:

- `TripPhase 1 -> 0..N TravelerPhaseProgress`

O que significa:

- a mesma fase pode ter progresso para vários viajantes

Exemplo:

- `PH1 = Visa`
- `PP1 = TT1 + PH1`
- `PP2 = TT2 + PH1`

Leitura:

- a fase é a mesma
- o progresso muda por viajante

## Relações `N:N` resolvidas no modelo

Algumas relações de negócio são naturalmente muitos-para-muitos, mas o banco resolve isso com tabelas intermediárias.

### `users` <-> `trips`

É resolvida por:

- `trip_travelers`

Leitura:

- vários usuários podem estar em várias viagens
- a tabela `trip_travelers` materializa cada combinação válida

### `trip_travelers` <-> `trip_phase_checklist_items`

É resolvida por:

- `traveler_checklist_progress`

Leitura:

- vários viajantes podem passar pelos mesmos itens
- e cada item pode existir para vários viajantes

### `trip_travelers` <-> `trip_phases`

É resolvida por:

- `traveler_phase_progress`

Leitura:

- vários viajantes passam por várias fases
- a tabela de progresso guarda o estado individual de cada combinação
