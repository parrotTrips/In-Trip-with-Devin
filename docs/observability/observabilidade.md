# Observabilidade — Parrot Trips

Documento de referência para discutir o que implementar, em que ordem, com que esforço e onde você veria cada coisa.

---

## Estado atual

O projeto não tem nenhuma camada de observabilidade configurada. O que existe hoje:

- `print()` no backend para alguns eventos do fluxo de OTP/WhatsApp (ex: `[WhatsApp] API error 500`)
- O Cloud Run coleta stdout/stderr automaticamente no Google Cloud Logging, então esses `print`s já aparecem lá — mas de forma não estruturada e sem contexto (sem `phone`, sem `trip_id`)
- Nenhum rastreamento de erros no frontend
- Nenhuma analytics de uso

> **Sobre Firebase**: não usamos Firebase. Os arquivos `firebase-debug.log` na raiz e em `frontend/` são resquício de uma tentativa em maio/2026 de adicionar o projeto GCP ao Firebase que não foi adiante. Não há nenhum SDK do Firebase no `package.json` nem importado no código.

---

## Três camadas de observabilidade

### Camada 1 — Técnica: "o que quebrou"

> Exemplos: "tal número de telefone não conseguiu logar", "a API retornou 500 para 3 usuários ontem"

Essa é a camada mais urgente antes de ter viajantes reais usando o app.

#### 1a. Logs estruturados no backend (~2–3h)

**O que é:** Substituir os `print()` por logs em JSON usando o módulo padrão `logging` do Python, com campos como `phone`, `trip_id`, `event`, `error`. O Cloud Run já captura tudo que vai para stdout — a diferença é que o Cloud Logging consegue **filtrar e buscar** por campo quando o formato é JSON.

**Esforço:** Baixo. É uma refatoração pontual em `auth_service.py` e nos outros serviços. Não muda a lógica de nada.

**Onde você veria:**
- Google Cloud Console → Logging → Logs Explorer
- Filtra por: `resource.type="cloud_run_revision"` e `jsonPayload.phone="+5511..."` para ver tudo que aconteceu com um número específico

**Exemplo do que você ganharia:**
```
{ "event": "otp_requested", "phone": "+5511999999999", "whatsapp_sent": false, "error": "timeout" }
{ "event": "otp_verified", "phone": "+5511999999999", "user_id": "abc-123" }
{ "event": "login_failed", "phone": "+5511888888888", "reason": "phone_not_authorized" }
```

---

#### 1b. Alertas automáticos (~1h, depois de 1a estar feito)

**O que é:** No Google Cloud Monitoring, criar uma métrica baseada nos logs (ex: contar logs com `event=login_failed`) e disparar um alerta por e-mail se passar de X por hora.

**Esforço:** Baixo uma vez que os logs estão estruturados.

**Onde você veria:** E-mail configurado no alerta, ou painel no Cloud Monitoring.

---

#### 1c. Rastreamento de erros no frontend — Sentry (~3–4h)

**O que é:** Sentry é uma ferramenta que captura erros JavaScript não tratados no app. Quando um viajante tem um crash ou um erro de rede que o app engoliu silenciosamente, o Sentry registra o stacktrace completo, o dispositivo, o que o usuário estava fazendo.

**Esforço:** Instalar o SDK (`@sentry/react`), inicializar no `main.tsx` com o DSN do projeto, e envolver o router com o `ErrorBoundary` do Sentry. Pronto.

**Onde você veria:** sentry.io — dashboard com cada erro, quantas pessoas foram afetadas, quando começou, stacktrace.

**Plano gratuito:** 5.000 erros/mês, mais que suficiente para o volume atual.

---

### Camada 2 — Produto: "o que as pessoas fazem"

> Exemplos: "quanto tempo cada pessoa passa em cada tela", "qual seção do roteiro é mais acessada", "alguém abre as Recomendações?"

Essa camada responde perguntas de produto — o que vale a pena melhorar, o que ninguém usa.

#### 2a. PostHog para analytics de uso (~4–6h)

**O que é:** PostHog é uma plataforma open-source de product analytics. Tem plano cloud gratuito (1M de eventos/mês). O SDK de React permite registrar automaticamente qual tela o usuário está, quanto tempo ficou, e eventos customizados como "abriu accordion de atividade", "clicou em mapa".

**Por que PostHog e não Google Analytics/Firebase Analytics:**
- Firebase Analytics: precisaria ativar o Firebase no projeto (atualmente não usamos) e configurar hosting ou usar o SDK via CDN — overhead desnecessário
- Google Analytics: focado em web, não em produto — os reports são menos úteis para entender comportamento dentro de um app
- PostHog: feito para produto, SDK de React nativo, dashboard de funis e retenção, e você pode self-hostar se quiser

**Esforço:** Instalar `posthog-js`, inicializar no `main.tsx`, e adicionar `useEffect` no router para disparar `posthog.capture('screen_view', { screen: '/day/:id' })` em cada mudança de rota. Eventos de clique específicos são opcionais e adicionados por tela conforme interesse.

**Onde você veria:** app.posthog.com (ou instância self-hosted) — dashboards de sessão, funis, heatmaps de clique, retenção por cohort.

**Exemplos de perguntas que você consegue responder:**
- "De cada 10 viajantes que abrem o app no primeiro dia de viagem, quantos chegam a ver os detalhes de uma atividade?"
- "Qual aba do bottom nav é mais clicada?"
- "A tela de Notificações é visitada ou ignorada?"

---

#### 2b. Eventos customizados de alto valor (+1–2h por tela, feito sob demanda)

Depois de ter o PostHog instalado, você pode adicionar eventos específicos onde quiser sem esforço de infraestrutura:

- `accordion_opened` → qual seção do roteiro (Manhã/Tarde/Noite) as pessoas mais abrem
- `checklist_item_checked` → quais atividades do checklist mais completadas
- `staff_profile_viewed` → qual guia mais clicado
- `recommendation_opened` → se a seção de recomendações é usada

---

### Camada 3 — Negócio: "a viagem funcionou?"

> Métricas de alto nível: % de viajantes que logaram antes da viagem, taxa de uso diário, etc.

#### 3a. Dashboard interno na página `/admin` (~1 dia)

**O que é:** Uma página no painel admin existente que mostra métricas agregadas por viagem: quantos viajantes cadastrados, quantos já logaram ao menos uma vez, % de checklist completo, etc.

**Esforço:** Médio. Requer novas queries no banco (contagens simples) e uma tela nova no frontend admin.

**Onde você veria:** Diretamente no painel `/admin` do app, acessível pelo staff.

**Quando faz sentido:** Quando tiver volume de viagens suficiente para que essas métricas contem uma história. Para o lançamento inicial, a Camada 1 é mais prioritária.

---

## Ordem de prioridade recomendada

| Prioridade | Item | Esforço | Valor |
|---|---|---|---|
| 1 | Logs estruturados no backend | ~2–3h | Diagnóstico imediato de falhas de login |
| 2 | Sentry no frontend | ~3–4h | Captura erros que viajantes nunca reportariam |
| 3 | Alertas no Cloud Monitoring | ~1h | Proativo — você sabe antes do viajante reclamar |
| 4 | PostHog analytics | ~4–6h | Entender o que funciona no produto |
| 5 | Eventos customizados por tela | +1–2h/tela | Perguntas específicas de produto |
| 6 | Dashboard admin de negócio | ~1 dia | Quando tiver volume |

---

## Resumo de onde você veria cada coisa

| Ferramenta | URL | O que você encontra lá |
|---|---|---|
| Google Cloud Logging | console.cloud.google.com → Logging | Logs do backend, filtrável por campos JSON |
| Google Cloud Monitoring | console.cloud.google.com → Monitoring | Alertas, métricas de erro e latência |
| Sentry | sentry.io | Erros do frontend, stacktraces, impacto por usuário |
| PostHog | app.posthog.com | Telas visitadas, tempo de sessão, eventos de clique |
| Painel /admin | No próprio app | Métricas de negócio por viagem |
