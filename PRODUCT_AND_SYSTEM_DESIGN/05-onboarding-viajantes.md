# Onboarding de Viajantes: Autenticação e Vínculo com Dados WeTravel

## Contexto

O app autentica viajantes via WhatsApp OTP. Para receber o OTP, o telefone do viajante precisa estar pré-cadastrado na tabela `users` do banco.

Os dados de compra vêm da WeTravel e identificam participantes por **email**. Após confirmar em todas as tabelas e payloads JSON da WeTravel (`wetravel_bookings`, `wetravel_trips`, `wetravel_order_options`, `wetravel_payments`, `wetravel_transactions`, `wetravel_leads`), **a WeTravel não fornece número de telefone dos participantes** em nenhum momento — nem no webhook, nem no `participants_json`.

Isso cria uma lacuna: o app precisa do telefone WhatsApp do viajante, mas a fonte de dados de compra não o possui.

## Problema

Sem o telefone do viajante cadastrado em `users`, ele não consegue:
1. Receber o OTP via WhatsApp.
2. Fazer login no app.
3. Ver os dados da sua viagem.

## Opções em Discussão

### Opção A — Importação manual pelo time Parrot Trips

O time coleta o número WhatsApp de cada viajante por outros canais (email pós-compra, grupo WhatsApp, planilha) e insere manualmente na tabela `users` antes de liberar acesso ao app.

**Prós:** Simples de implementar, sem mudança no fluxo de compra.

**Contras:** Operação manual por viagem, escalabilidade limitada, risco de erro humano.

---

### Opção B — Formulário pós-compra (fora do app)

Após a confirmação da compra na WeTravel, o viajante recebe um link (email ou WhatsApp) para preencher o número de WhatsApp. O backend registra automaticamente em `users`.

**Prós:** Automatizável, experiência integrada ao fluxo de compra.

**Contras:** Requer um formulário externo ou integração com o fluxo de onboarding da WeTravel.

---

### Opção C — Cadastro no primeiro acesso via convite

O viajante recebe um link de convite único (ex: `app.parrottrips.com/join?token=...`). Ao acessar, ele informa o próprio número WhatsApp e o email usado na compra. O backend valida o email na WeTravel, cria o usuário e inicia o fluxo de OTP.

**Prós:** Self-service, escalável, sem operação manual recorrente.

**Contras:** Mais complexo de implementar, requer geração e gestão de tokens de convite.

---

### Opção D — Autenticação por email (alternativa ao WhatsApp OTP)

Em vez de autenticar por telefone, o app envia um magic link ou OTP por **email**, que a WeTravel já possui para todos os participantes. O WhatsApp OTP continuaria disponível para quem preferir.

**Prós:** Elimina completamente a lacuna de telefone, usa dado que a WeTravel já fornece.

**Contras:** Requer mudança na estratégia de autenticação já implementada, dependência de entregabilidade de email.

---

## Pergunta Central para Stakeholders

> Como os viajantes saberão que têm acesso ao app e como fornecerão o número WhatsApp (ou preferimos mudar para autenticação por email)?

## Decisão

_A definir._

## Impacto no Desenvolvimento

Enquanto essa decisão não é tomada, o fluxo de onboarding de viajantes está bloqueado. O desenvolvimento pode prosseguir em:
- Tela do staff (Marcelo e Vitor já têm acesso).
- View `v_traveler_app_profile` no Supabase.
- Endpoints e telas que serão usados após o viajante estar cadastrado.
