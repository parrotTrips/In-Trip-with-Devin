# Metricas e Observabilidade - Parrot Trips

Este documento explica, em linguagem operacional, para que serve cada ferramenta de metricas e observabilidade do Parrot Trips, que tipo de informacao cada uma mostra e quando usar cada painel.

O projeto esta organizado em tres camadas:

| Camada | Ferramenta | Responde principalmente |
|---|---|---|
| Produto | PostHog | O que os viajantes fazem no app? |
| Erros do frontend | Sentry | O app quebrou para alguem? Onde? |
| Backend e infraestrutura | Cloud Logging | O que aconteceu na API, login, OTP e WhatsApp? |

## 1. PostHog - metricas de uso e comportamento

O PostHog mede comportamento de produto. Ele registra eventos quando uma pessoa navega, clica, abre secoes, marca checklist ou interage com recomendacoes.

Use o PostHog quando a pergunta for sobre uso:

| Pergunta | Como pensar |
|---|---|
| Quantas pessoas abriram o app? | Contar usuarios unicos no evento `tela_visitada` |
| Quais telas sao mais usadas? | Quebrar `tela_visitada` por `tela` |
| O checklist esta sendo usado? | Contar `checklist_item_marcado` e `fase_concluida` |
| Quais atividades chamam mais atencao? | Quebrar `atividade_expandida` por `atividade_nome` |
| As recomendacoes locais geram acao? | Ver `recommendation_opened`, `recommendation_call_clicked`, `recommendation_whatsapp_clicked` |
| Alguem enviou feedback? | Contar `app_feedback_sent` |

Eventos que o app ja envia:

| Evento | Quando acontece |
|---|---|
| `tela_visitada` | Quando o usuario muda de rota/tela |
| `aba_nav_clicada` | Quando clica na navegacao inferior |
| `secao_informacao_aberta` | Quando abre uma secao da tela de informacoes |
| `checklist_item_marcado` | Quando marca um item do checklist |
| `checklist_item_desmarcado` | Quando desmarca um item do checklist |
| `fase_concluida` | Quando conclui uma fase |
| `atividade_expandida` | Quando abre detalhes de uma atividade |
| `activity_maps_opened` | Quando abre mapa de uma atividade |
| `recommendation_opened` | Quando abre uma recomendacao local |
| `recommendation_call_clicked` | Quando clica para ligar para uma recomendacao |
| `recommendation_whatsapp_clicked` | Quando clica para chamar uma recomendacao no WhatsApp |
| `recommendation_phone_copied` | Quando copia o telefone de uma recomendacao |
| `app_feedback_sent` | Quando envia feedback pelo app |

Contextos registrados:

| Campo | Significado |
|---|---|
| `viagem_id` | Identificador da viagem no WeTravel |
| `modo_viagem` | Estado da viagem, como `pre-trip` ou `in-trip` |
| `telefone`, `nome`, `papel` | Dados associados ao usuario identificado no login |

Leitura importante: PostHog mede comportamento, nao necessariamente satisfacao. Se uma tela tem poucos acessos, pode ser baixa relevancia, baixa visibilidade ou problema de navegacao. A metrica aponta onde investigar.

## 2. Sentry - erros e crashes no frontend

O Sentry captura erros tecnicos do app React. Ele ajuda a descobrir quando o app quebrou no navegador de alguem, em qual linha do codigo, em qual dispositivo e com qual usuario.

Use o Sentry quando a pergunta for sobre erro no app:

| Pergunta | Como pensar |
|---|---|
| O app quebrou para alguem? | Ver Issues recentes |
| Quantas pessoas foram afetadas? | Ver contagem de users por issue |
| Onde quebrou? | Ver stacktrace |
| O que a pessoa fez antes? | Ver breadcrumbs |
| Foi um erro isolado ou recorrente? | Ver frequencia e ultima ocorrencia |

O app inicializa o Sentry no frontend quando existe `VITE_SENTRY_DSN`. No login, o usuario tambem e associado ao Sentry com `Sentry.setUser(...)`. Isso permite que erros sejam ligados a um usuario identificado.

Leitura importante: Sentry e para falhas tecnicas. Ele nao deve ser usado como ferramenta principal de produto. Um usuario pode abandonar uma tela sem gerar erro; isso aparece melhor no PostHog.

## 3. Cloud Logging - logs do backend

O Cloud Logging mostra o que aconteceu no backend rodando no Cloud Run. Ele e usado para investigar autenticacao, OTP, WhatsApp, tokens JWT e erros da API.

Use Cloud Logging quando a pergunta for sobre backend:

| Pergunta | Como pensar |
|---|---|
| Por que um usuario nao conseguiu logar? | Filtrar logs pelo telefone |
| O OTP foi gerado? | Procurar `otp_gerado` |
| O WhatsApp enviou ou falhou? | Procurar `whatsapp_enviado`, `whatsapp_falhou`, `whatsapp_excecao` |
| O token estava ausente ou expirado? | Procurar eventos de JWT |
| A API teve erro tecnico? | Ver logs do Cloud Run no periodo do problema |

Eventos estruturados que o backend ja registra:

| Evento | Significado |
|---|---|
| `login_ok` | Usuario logou com sucesso |
| `otp_gerado` | Codigo OTP foi criado |
| `whatsapp_enviado` | Mensagem enviada para a API do WhatsApp com sucesso |
| `whatsapp_falhou` | API do WhatsApp recusou ou retornou erro |
| `whatsapp_excecao` | Falha de rede, timeout ou excecao no envio |
| `login_numero_nao_autorizado` | Telefone nao encontrado/autorizado |
| `otp_invalido` | Codigo digitado nao confere |
| `otp_expirado` | Codigo venceu |
| `jwt_ausente` | Requisicao sem token |
| `jwt_payload_invalido` | Token sem payload esperado |
| `jwt_invalido_ou_expirado` | Token invalido ou vencido |

Filtro base no Logs Explorer:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="parrot-trips-backend"
```

Exemplo para investigar um telefone:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="parrot-trips-backend"
jsonPayload.telefone="+5511999999999"
```

Exemplo para problemas de WhatsApp:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="parrot-trips-backend"
jsonPayload.evento=~"whatsapp_falhou|whatsapp_excecao"
```

Leitura importante: Cloud Logging mostra o que o backend registrou. Se uma acao acontece somente no frontend e nao chama a API, ela provavelmente aparece no PostHog, nao no Cloud Logging.

## 4. Qual ferramenta abrir primeiro?

| Situacao | Primeira ferramenta |
|---|---|
| Quero saber se as pessoas usam o app | PostHog |
| Quero saber quais telas geram mais interesse | PostHog |
| Quero medir checklist, recomendacoes ou feedback | PostHog |
| Um viajante disse que o app travou | Sentry |
| Quero saber qual erro JS aconteceu | Sentry |
| Um viajante nao recebeu OTP | Cloud Logging |
| Um telefone nao consegue logar | Cloud Logging |
| Quero saber se WhatsApp falhou | Cloud Logging |

## 5. Metricas iniciais para discutir com o time

Sugestao de primeiro painel de metricas:

| Metrica | Ferramenta | Evento/fonte |
|---|---|---|
| Usuarios unicos que abriram o app | PostHog | `tela_visitada`, unique users |
| Telas mais acessadas | PostHog | `tela_visitada` por `tela` |
| Uso do menu inferior | PostHog | `aba_nav_clicada` por `aba` |
| Uso do checklist | PostHog | `checklist_item_marcado`, `fase_concluida` |
| Atividades mais abertas | PostHog | `atividade_expandida` por `atividade_nome` |
| Uso de recomendacoes locais | PostHog | eventos `recommendation_*` |
| Feedback enviado | PostHog | `app_feedback_sent` |
| Erros frontend por usuario afetado | Sentry | Issues |
| Falhas de login/OTP/WhatsApp | Cloud Logging | eventos estruturados do backend |

## 6. Perguntas para validar com o time

Antes de montar dashboards definitivos, vale decidir:

1. Quais metricas importam antes da viagem?
2. Quais metricas importam durante a viagem?
3. O time quer olhar por viagem, por usuario ou por periodo?
4. Quais eventos indicam sucesso real, e quais sao apenas curiosidade?
5. Quais alertas precisam acionar alguem imediatamente?

Uma boa regra: dashboard deve responder perguntas recorrentes. Investigacao pontual pode ficar em filtros salvos, sem virar painel permanente.
