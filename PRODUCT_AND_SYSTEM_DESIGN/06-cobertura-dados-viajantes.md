# Cobertura de Dados dos Viajantes

## Contexto

Antes de conectar os endpoints do backend às telas do app, foi feito um teste de sanidade para entender quantos dos viajantes ativos no Supabase têm dados suficientes para usar o app.

A fonte de verdade para participantes ativos é a view `host_trip_participants`. O dashboard da Parrot Trips mostra 161 viajantes ativos e 167 purchases — a diferença entre os dois números existe porque um mesmo viajante pode ter múltiplas purchases (ex: pacote + add-on como linhas separadas).

## Resultado do Teste de Sanidade (maio 2026)

| Medição | Qtd |
|---|---|
| Participantes ativos únicos (`host_trip_participants`) | 156 |
| Purchases totais (múltiplas por pessoa possível) | 167 |
| Com telefone em `wetravel_participant_phones` | 153 |
| Cadastrados em `users` como traveler | 152 |

## Os 4 Participantes Faltantes

### Sem telefone cadastrado na WeTravel (3 pessoas)

Provavelmente não preencheram o campo de WhatsApp no checkout. Todos da viagem **GSB NYE Brazil Trek** (trip_uuid: `2425416057`):

| Nome | Email |
|---|---|
| Ariana Lee | alee20@stanford.edu |
| Luke Zerrer | luke.zerrer@gmail.com |
| Kyle McGovern | Mcgovern.Kyle.t@gmail.com |

**Ação necessária:** entrar em contato para coletar o número de WhatsApp e inserir manualmente em `users`.

### Com telefone duplicado (1 pessoa não resolvida)

Existem 3 pares de participantes que cadastraram o mesmo número de WhatsApp na WeTravel — provavelmente casais ou companheiros de viagem. Para cada par, apenas o primeiro (por ordem alfabética de email) foi inserido em `users`. O segundo ficou bloqueado pelo constraint `UNIQUE` no campo `phone`.

| Par | Phone compartilhado | Inserido | Bloqueado |
|---|---|---|---|
| Andre Rappaccioli / Valentina Losada | +12158479883 | arappa@wharton.upenn.edu | vlosada@wharton.upenn.edu |
| Jorge Engels / Olatoun Mosaku | +447785376627 | jengels@wharton.upenn.edu | ola.mosaku@outlook.com |
| Ben Veres / Jae Audrey Deguerrera | +13123585733 | ben.veres.13@gmail.com | jaudrey@stanford.edu |

**Ação necessária:** confirmar com cada par qual é o WhatsApp individual de cada um e atualizar `users` com o número correto.

## Conclusão

O app tem dados suficientes para **152 dos 156 viajantes ativos (97%)** entrarem e usarem o app. Os 4 restantes dependem de coleta manual de WhatsApp.

## Fonte dos Dados

- Participantes ativos: view `host_trip_participants` (`is_cancelled = false`)
- Telefones: tabela `wetravel_participant_phones` (populada automaticamente via pipeline de enriquecimento da WeTravel)
- Usuários do app: tabela `users` (`role = 'traveler'`)
- Vínculo com viagem: tabela `trip_travelers` (`wetravel_trip_uuid`)
