# Dicionário de Dados

Este documento descreve o modelo atual do banco em alto nível, tabela por tabela, campo por campo, com foco no motivo de cada informação existir.

O objetivo aqui não é detalhar tipo SQL ou constraint, e sim explicar a intenção de negócio de cada campo.

## `users`

Representa o viajante como identidade global no sistema.

- `id`: identificador único e estável do viajante.
- `phone`: telefone principal do viajante. Hoje também funciona como identificador de acesso e contato.
- `full_name`: nome completo global da pessoa.
- `email`: e-mail global do viajante.
- `status`: estado da conta do viajante no sistema.
- `created_at`: quando o registro do viajante foi criado.
- `updated_at`: quando o registro do viajante foi atualizado pela última vez.

## `trips`

Representa a viagem em si, como entidade central do conteúdo e da operação.

- `id`: identificador único da viagem.
- `name`: nome principal da viagem.
- `short_name`: nome curto para contextos de interface com menos espaço.
- `description`: descrição geral da viagem.
- `start_date`: data oficial de início da viagem.
- `end_date`: data oficial de fim da viagem.
- `status`: estado atual da viagem no ciclo de vida do produto.
- `created_at`: quando a viagem foi cadastrada.
- `updated_at`: quando a viagem foi alterada pela última vez.

## `trip_travelers`

Representa o vínculo entre um viajante e uma viagem. Essa tabela existe para materializar o conceito de "este viajante dentro desta viagem".

- `id`: identificador único desse vínculo.
- `trip_id`: viagem à qual o viajante está associado.
- `user_id`: viajante associado à viagem.
- `created_at`: quando esse vínculo foi criado.
- `updated_at`: quando esse vínculo foi alterado pela última vez.

## `traveler_profiles`

Guarda dados pessoais e operacionais do viajante no contexto de uma viagem específica.

- `id`: identificador único do perfil.
- `trip_traveler_id`: vínculo com o registro do viajante dentro da viagem.
- `preferred_name`: nome pelo qual o viajante prefere ser chamado.
- `date_of_birth`: data de nascimento.
- `gender`: informação cadastral do viajante.
- `passport_first_name`: primeiro nome exatamente como está no passaporte.
- `passport_last_name`: sobrenome exatamente como está no passaporte.
- `passport_country`: país emissor do passaporte.
- `passport_number`: número do passaporte.
- `passport_issue_date`: data de emissão do passaporte.
- `passport_expiration_date`: data de validade do passaporte.
- `dietary_restrictions_flag`: indica se existe alguma restrição alimentar.
- `dietary_restrictions_details`: detalha a restrição alimentar quando existir.
- `seasickness_flag`: indica se o viajante tem tendência a enjoo marítimo.
- `plus_one_flag`: indica se existe acompanhante.
- `plus_one_name`: nome do acompanhante.
- `plus_one_email`: e-mail do acompanhante.
- `needs_flight_help_flag`: indica se o viajante precisa de ajuda com voo.
- `flight_help_details`: detalha o tipo de ajuda necessária com voo.
- `needs_travel_insurance_help_flag`: indica se o viajante precisa de ajuda com seguro viagem.
- `unforgettable_trip_details`: campo aberto para expectativas, desejos ou preferências sobre a viagem.
- `created_at`: quando o perfil foi criado.
- `updated_at`: quando o perfil foi atualizado pela última vez.

## `traveler_products`

Guarda dados comerciais e operacionais da compra do viajante dentro da viagem.

- `id`: identificador único do registro comercial.
- `trip_traveler_id`: vínculo com o viajante dentro da viagem.
- `package_name`: nome do pacote comprado.
- `room_type`: tipo de quarto ou acomodação associado à compra.
- `amount_paid_usd`: valor pago pelo viajante em dólar.
- `purchased_addons_summary`: resumo textual dos extras comprados.
- `service_agreement_media_asset_id`: referência ao arquivo do contrato ou service agreement.
- `created_at`: quando o registro foi criado.
- `updated_at`: quando o registro foi atualizado pela última vez.

## `media_assets`

Centraliza os arquivos usados pelo sistema, com foco no cenário atual de Google Drive.

- `id`: identificador único do ativo de mídia.
- `drive_file_id`: identificador estável do arquivo dentro do Google Drive.
- `drive_path`: caminho legível de pasta/subpasta para organização operacional.
- `public_url`: link público ou compartilhável do arquivo.
- `mime_type`: tipo do arquivo, como PDF, imagem ou vídeo.
- `original_filename`: nome original do arquivo no upload.
- `created_at`: quando o ativo foi registrado.
- `updated_at`: quando os metadados do ativo foram atualizados pela última vez.

## `trip_phases`

Representa as fases da jornada da viagem, tanto pré-viagem quanto durante a viagem.

- `id`: identificador único da fase.
- `trip_id`: viagem à qual a fase pertence.
- `parent_phase_id`: referência opcional para uma fase pai, permitindo hierarquia.
- `phase_type`: tipo da fase, como pré-viagem ou durante a viagem.
- `title`: título principal da fase.
- `subtitle`: subtítulo complementar da fase.
- `icon`: ícone usado para representar a fase na interface.
- `short_description`: descrição curta da fase.
- `detailed_description`: descrição mais completa com instruções ou contexto.
- `sort_order`: ordem em que a fase aparece.
- `starts_at`: início temporal da fase, quando aplicável.
- `ends_at`: fim temporal da fase, quando aplicável.
- `is_locked_by_default`: indica se a fase começa bloqueada.
- `is_visible`: indica se a fase deve aparecer para o viajante.
- `created_at`: quando a fase foi criada.
- `updated_at`: quando a fase foi atualizada pela última vez.

## `trip_phase_checklist_items`

Guarda os itens de checklist de cada fase.

- `id`: identificador único do item.
- `trip_phase_id`: fase à qual o item pertence.
- `label`: texto principal do item de checklist.
- `description`: detalhe complementar do item.
- `sort_order`: ordem de exibição do item dentro da fase.
- `is_required`: indica se o item é obrigatório ou apenas recomendado.
- `created_at`: quando o item foi criado.
- `updated_at`: quando o item foi atualizado pela última vez.

## `trip_phase_links`

Guarda links úteis associados a uma fase.

- `id`: identificador único do link.
- `trip_phase_id`: fase à qual o link pertence.
- `label`: texto exibido para o link.
- `url`: destino do link.
- `sort_order`: ordem de exibição do link na fase.
- `created_at`: quando o link foi criado.
- `updated_at`: quando o link foi atualizado pela última vez.

## `trip_activities`

Representa as atividades exibidas dentro de uma fase do tipo dia/itinerário.

- `id`: identificador único da atividade.
- `trip_phase_id`: fase à qual a atividade pertence.
- `name`: nome da atividade.
- `activity_type`: tipo da atividade, como incluída, opcional, sugerida ou logística.
- `starts_at`: momento de início da atividade, quando aplicável.
- `duration_minutes`: duração prevista da atividade em minutos.
- `short_description`: resumo da atividade.
- `practical_info`: informações práticas para o viajante.
- `amount_brl`: valor da atividade em reais, quando existir cobrança.
- `sort_order`: ordem de exibição da atividade.
- `created_at`: quando a atividade foi criada.
- `updated_at`: quando a atividade foi atualizada pela última vez.

## `activity_media`

Liga mídias às atividades.

- `id`: identificador único da mídia da atividade.
- `trip_activity_id`: atividade à qual a mídia pertence.
- `media_asset_id`: arquivo associado, vindo de `media_assets`.
- `media_type`: tipo de mídia exibida nessa atividade.
- `caption`: legenda ou texto de apoio da mídia.
- `sort_order`: ordem de exibição da mídia na atividade.
- `created_at`: quando a mídia foi vinculada à atividade.

## `traveler_checklist_progress`

Guarda o progresso individual do viajante em cada item de checklist.

- `id`: identificador único do progresso.
- `trip_traveler_id`: viajante dentro da viagem.
- `trip_phase_checklist_item_id`: item de checklist acompanhado.
- `is_completed`: indica se o item foi concluído.
- `completed_at`: quando o item foi concluído.
- `updated_at`: quando esse progresso foi atualizado pela última vez.

## `traveler_phase_progress`

Guarda o progresso individual do viajante no nível da fase inteira.

- `id`: identificador único do progresso da fase.
- `trip_traveler_id`: viajante dentro da viagem.
- `trip_phase_id`: fase acompanhada.
- `is_completed`: indica se a fase foi concluída.
- `completed_at`: quando a fase foi concluída.
- `updated_at`: quando esse progresso foi atualizado pela última vez.

## Observações gerais

- O modelo atual está focado em viajantes, sem papéis internos como admin, equipe ou backoffice.
- Comentários, notificações e anexos próprios de fase foram removidos do escopo atual.
- O armazenamento de mídia foi simplificado para o uso com Google Drive.
