# Contexto e Decisões

## Contexto

Quase todo o conteúdo do `Map` é igual para todos os viajantes.

O que muda por viajante é principalmente:

- progresso
- comentários
- perfil

O produto modelado aqui cobre apenas a experiência do viajante autenticado no app.

## Abordagem recomendada

A modelagem segue um modelo relacional híbrido, separando:

1. conteúdo compartilhado da viagem
2. participação do viajante na viagem
3. estado e interação por viajante
4. dados operacionais e comerciais do viajante

## Banco-alvo

- `PostgreSQL`

## Convenções

- tabelas no plural
- colunas em `snake_case`
- PK padrão `id`
- FK no padrão `<entidade>_id`
- `uuid` como identificador principal
- `timestamptz` para timestamps
- `text` + `check constraint` para status e tipos, em vez de enum do PostgreSQL nesta primeira fase

## Decisões fechadas

### Decisão 1

`traveler_profiles` é separado de `users`.

Motivo:

- o perfil exibido no app pertence à viagem, não apenas à pessoa global

### Decisão 2

`traveler_products` é separado de `traveler_profiles`.

Motivo:

- pacote, pagamento e service agreement têm natureza operacional/comercial

### Decisão 3

`trip_travelers` é o ponto central de todas as tabelas por-viajante-na-viagem.

Motivo:

- evita repetir `trip_id + user_id` em várias tabelas

### Decisão 4

Comentários existem apenas no nível de fase nesta primeira versão.

### Decisão 5

`trip_phases` representa tanto fases pré-viagem quanto os dias da viagem.

### Decisão 6

Checklist, links, anexos e atividades ficam ligados a `trip_phases`.

### Decisão 7

O banco atende exclusivamente o app do viajante nesta fase.

### Decisão 8

`users` representa apenas viajantes autenticados no escopo atual.

### Decisão 9

Métricas e eventos analíticos ficam fora do escopo inicial.

### Decisão 10

`traveler_profiles` permanece como uma tabela relativamente larga nesta primeira versão.
