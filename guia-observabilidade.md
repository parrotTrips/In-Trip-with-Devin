# Guia de Observabilidade — Parrot Trips

Três ferramentas ativas, cada uma com uma responsabilidade clara.

| Ferramenta | Pergunta que responde | Acesso |
|---|---|---|
| **Cloud Logging (GCP)** | O que quebrou no backend? | console.cloud.google.com |
| **Sentry** | O que quebrou no frontend? | sentry.io |
| **PostHog** | O que os viajantes fazem no app? | app.posthog.com |

---

## 1. Cloud Logging — erros e eventos do backend

### Como acessar

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Menu lateral → **Logging** → **Logs Explorer**
3. Cole este filtro base e pressione Enter:

```
resource.type="cloud_run_revision"
resource.labels.service_name="parrot-trips-backend"
```

Você verá todos os eventos do backend em tempo real.

### Eventos e o que significam

| Evento (`jsonPayload.evento`) | O que aconteceu | O que fazer |
|---|---|---|
| `login_ok` | Viajante logou com sucesso | ✅ Normal |
| `otp_gerado` | Código OTP foi criado e tentou enviar pelo WhatsApp | ✅ Normal |
| `whatsapp_enviado` | Mensagem chegou na API do WhatsApp com sucesso | ✅ Normal |
| `whatsapp_falhou` | API do WhatsApp recusou a mensagem | Ver `status_http` no log — 400 = número inválido, 500 = problema na Meta |
| `whatsapp_excecao` | Timeout ou falha de rede ao chamar o WhatsApp | Pode ser instabilidade pontual; se recorrente, verificar conectividade do Cloud Run |
| `login_numero_nao_autorizado` | Alguém tentou logar com um número que não está no banco | Verificar se o número precisa ser cadastrado na tabela `users` |
| `otp_invalido` | Código digitado errado | Ocasional é normal; frequente pode ser erro de UX |
| `otp_expirado` | Demorou mais de 10 minutos para digitar o código | Normal; viajante pode pedir novo código |
| `jwt_ausente` | Chamada à API sem token de autenticação | Pode ser bug no app ou tentativa externa |
| `jwt_invalido_ou_expirado` | Token vencido (após 14 dias) ou adulterado | Normal após 14 dias; frequente = possível bug no app |

### Filtros úteis

**Ver tudo de um número específico:**
```
resource.type="cloud_run_revision"
jsonPayload.telefone="+5511999999999"
```

**Ver só falhas de login:**
```
resource.type="cloud_run_revision"
jsonPayload.evento="login_numero_nao_autorizado"
```

**Ver só problemas com WhatsApp:**
```
resource.type="cloud_run_revision"
jsonPayload.evento=~"whatsapp_falhou|whatsapp_excecao"
```

**Ver os últimos 30 minutos:**
No canto superior direito do Logs Explorer, mude o período de tempo para "Last 30 minutes".

### Como criar um alerta automático

Para receber e-mail quando muitos logins falharem:

1. No Logs Explorer, configure o filtro com o evento que quer monitorar
2. Clique em **Create alert** (no topo da página)
3. Defina: "se aparecer mais de 5 vezes em 10 minutos"
4. Adicione seu e-mail como destino

---

## 2. Sentry — crashes e erros do frontend

### Como acessar

1. Acesse [sentry.io](https://sentry.io)
2. Selecione o projeto **parrot-trips-frontend**
3. Menu lateral → **Issues**

### O que você vê na tela de Issues

Cada linha é um tipo de erro agrupado. As colunas mais importantes:

- **Events** — quantas vezes esse erro aconteceu no total
- **Users** — quantos viajantes diferentes foram afetados
- **First seen / Last seen** — quando começou e quando foi a última vez

### Como interpretar

**Prioridade alta** (resolver antes de uma viagem):
- Erros com "Users" alto → muita gente está sendo afetada
- Erros em telas críticas: login, roteiro principal, checklist
- Erros que aparecem repetidamente (Events crescendo)

**Pode ignorar:**
- Erros que começam com `chrome-extension://` → vêm de extensões do browser, não do app
- `Failed to fetch` esporádico → WiFi instável do viajante
- Erros com 0 usuários → pode ser um bot ou teste

### Quando clicar em um erro

Você vê:
- **Stacktrace** — a linha exata do código onde quebrou
- **Breadcrumbs** — o que o usuário fez antes do erro (cliques, navegação)
- **Tags** — o dispositivo, navegador, e qual usuário foi afetado (se identificado)

Isso permite reproduzir o problema: "o erro acontece quando o usuário vai de HomeScreen para DayDetails e o dia não tem atividades cadastradas."

### Identificar qual viajante foi afetado

Se o viajante estava logado quando o erro aconteceu, o Sentry mostra o nome/telefone dele. Acesse **User** no painel do erro para ver quem foi.

---

## 3. PostHog — comportamento dos viajantes

### Como acessar

1. Acesse [app.posthog.com](https://app.posthog.com)
2. Selecione o projeto **Parrot Trips**

### Eventos registrados pelo app

| Evento | Quando dispara | Dados extras |
|---|---|---|
| `tela_visitada` | Toda mudança de tela | `tela` (ex: `/`, `/day/abc`, `/profile`) |
| `aba_nav_clicada` | Clique no menu inferior | `aba` (Journey / My Profile / Information) |
| `secao_informacao_aberta` | Abertura de seção na tela Information | `secao` (Parrot Team, FAQ, Cancellation Policy, …) |
| `checklist_item_marcado` | Viajante marca um item do checklist | `item_label`, `fase_titulo` |
| `checklist_item_desmarcado` | Viajante desmarca um item | `item_label`, `fase_titulo` |
| `fase_concluida` | Viajante clica "Mark as Completed" | `fase_titulo` |
| `atividade_expandida` | Viajante abre os detalhes de uma atividade | `atividade_nome`, `atividade_tipo` |

Além dos eventos, todo evento carrega automaticamente:
- `viagem_id` — qual viagem o viajante está
- `modo_viagem` — `pre-trip` ou `in-trip`

### Respondendo perguntas de negócio

---

**"Quantas pessoas da viagem X já abriram o app?"**

Insights → Trends
- Evento: `tela_visitada`
- Filtro: `viagem_id = [id da viagem]`
- Métrica: **Unique users**

---

**"Quando as pessoas mais acessam? De manhã, à noite?"**

Insights → Trends
- Evento: `tela_visitada`
- Período: durante a viagem
- Break down by: **Hour of day**

Você verá um gráfico com os picos de acesso por hora.

---

**"As pessoas acessam durante a viagem ou só antes?"**

Insights → Trends
- Evento: `tela_visitada`
- Break down by: `modo_viagem`

Compara o volume com `pre-trip` vs `in-trip`.

---

**"Quantas vezes cada pessoa entrou no app?"**

People → busca pelo nome ou telefone → aba **Sessions**

Você vê cada sessão com data e hora.

---

**"Qual parte do app as pessoas mais usam?"**

Insights → Trends
- Evento: `aba_nav_clicada`
- Break down by: `aba`

Você vê quantos cliques cada aba recebeu: Journey, My Profile, Information.

---

**"Alguém usa o checklist?"**

Insights → Trends
- Evento: `checklist_item_marcado`
- Métrica: Unique users

Se o número for baixo em relação ao total de viajantes, o checklist não está sendo usado.

---

**"Quais atividades mais chamam atenção?"**

Insights → Trends
- Evento: `atividade_expandida`
- Break down by: `atividade_nome`

Você vê quais atividades as pessoas mais clicam para ver detalhes.

---

**"Alguém viu a política de cancelamento?"**

Insights → Trends
- Evento: `secao_informacao_aberta`
- Filtro: `secao = Cancellation Policy`

---

**"Histórico completo de um viajante?"**

People → busca pelo telefone ou nome → aba **Events**

Você vê cada ação que a pessoa fez no app, em ordem cronológica.

---

**"Quanto tempo cada sessão dura?"**

Insights → Trends
- Métrica: **Session duration** (não é evento, é calculado automaticamente)

---

### Sobre cancelamentos e transferências

O app mostra a política de cancelamento mas não captura o motivo real — esse dado fica no WeTravel (onde a compra foi feita). O que você consegue saber pelo app é **quem e quando abriu a seção de política de cancelamento**, que funciona como sinal de intenção. Para saber quem efetivamente cancelou ou transferiu, consulte o painel do WeTravel.

---

## Resumo: qual ferramenta para qual situação

| Situação | Ferramenta |
|---|---|
| "Um viajante disse que não consegue logar" | Cloud Logging → filtrar pelo telefone dele |
| "O app travou para alguém" | Sentry → Issues → buscar pelo nome do viajante |
| "Quantas pessoas usaram o app hoje?" | PostHog → Insights → `tela_visitada` unique users |
| "O WhatsApp está funcionando?" | Cloud Logging → filtrar `whatsapp_falhou` |
| "A tela X está com bug?" | Sentry → Issues → filtrar pela tela |
| "As pessoas usam o checklist?" | PostHog → Insights → `checklist_item_marcado` |
| "Qual parte do app mais engaja?" | PostHog → Insights → `aba_nav_clicada` |
