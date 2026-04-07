# Mídia e Storage

## Decisão principal

Arquivos e mídias não devem ser salvos diretamente no banco como estratégia principal.

Direção recomendada:

- `PostgreSQL` para dados relacionais
- Google Drive para arquivos e imagens
- banco guardando apenas referência e metadados

## Por que não salvar mídia direto no banco

Embora seja possível usar o banco para armazenar binários, isso não é a melhor opção para este projeto.

Problemas principais:

- banco fica mais pesado
- backup e restore ficam mais caros
- servir arquivos fica menos eficiente
- escala pior no médio prazo

## Organização escolhida

Os arquivos serão organizados em Google Drive com pastas e subpastas.

O banco não precisa modelar a árvore completa de pastas.

Ele só precisa guardar a referência principal do arquivo e um caminho legível para organização operacional.

## O que fica no banco

Na entidade `media_assets`, o banco deve armazenar:

- `id`
- `drive_file_id`
- `drive_path`
- `public_url`
- `mime_type`
- `original_filename`
- `created_at`
- `updated_at`

## O que fica no Google Drive

- imagens de atividades
- anexos de fases
- PDFs
- service agreement
- possíveis vídeos futuros

## Relação com o modelo

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
- mantém a referência do arquivo alinhada com a organização por pastas no Drive
