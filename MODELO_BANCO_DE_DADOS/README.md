# Modelagem do Banco de Dados

Este diretório concentra a modelagem do banco de dados do projeto, separada por tema para facilitar leitura, discussão e revisão.

## Ordem sugerida de leitura

1. [Contexto e Decisões](./01-contexto-e-decisoes.md)
2. [ERD Conceitual](./02-erd-conceitual.md)
3. [Modelo Lógico](./03-modelo-logico.md)
4. [Modelo para Vertabelo](./04-vertabelo.md)
5. [Cardinalidades](./05-cardinalidades.md)
6. [Mídia e Storage](./06-midia-e-storage.md)
7. [Dicionário de Dados](./07-dicionario-de-dados.md)
8. [Relações Explicadas](./08-relacoes-explicadas.md)

## Objetivo

O objetivo desta documentação é servir como base para:

- discussão com o time
- desenho visual no Vertabelo
- futura implementação em PostgreSQL

## Escopo atual

O banco deve cobrir o que existe no app hoje:

- viagens
- conteúdo exibido no `Map`
- fases pré-viagem e durante a viagem
- atividades por fase/dia
- checklist
- autenticação
- perfil do viajante dentro da viagem
- dados operacionais e comerciais do viajante

Fora do escopo inicial:

- métricas e eventos analíticos
- `Secret Missions`
- `Sharing XP`
- `Local Recommendations` como módulo separado
- `Emergency Contacts` como módulo separado
- `Documents` como módulo separado
