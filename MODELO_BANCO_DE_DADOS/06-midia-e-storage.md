# Mídia e Storage

## Decisão principal

Arquivos e mídias não devem ser salvos diretamente no banco como estratégia principal.

Direção recomendada:

- `PostgreSQL` para dados relacionais
- storage externo para arquivos e imagens
- banco guardando apenas referência e metadados

## Por que não salvar mídia direto no banco

Embora seja possível usar o banco para armazenar binários, isso não é a melhor opção para este projeto.

Problemas principais:

- banco fica mais pesado
- backup e restore ficam mais caros
- servir arquivos fica menos eficiente
- escala pior no médio prazo

## O que fica no banco

Na entidade `media_assets`, o banco deve armazenar:

- `id`
- `storage_provider`
- `storage_bucket`
- `storage_key`
- `public_url`
- `mime_type`
- `original_filename`
- `file_size_bytes`
- `created_at`
- `updated_at`

## O que fica no storage

- imagens de atividades
- anexos de fases
- PDFs
- service agreement
- possíveis vídeos futuros

## Relação com o modelo

### `trip_phase_attachments`

Não guarda `file_url` diretamente.

Deve referenciar:

- `media_asset_id`

### `activity_media`

Não guarda `url` diretamente.

Deve referenciar:

- `media_asset_id`

### `traveler_products`

Não guarda `service_agreement_url` diretamente.

Deve referenciar:

- `service_agreement_media_asset_id`

## Benefício do modelo

Usar `media_assets`:

- evita duplicação
- centraliza metadados de arquivo
- facilita reaproveitamento
- deixa o ERD mais limpo
