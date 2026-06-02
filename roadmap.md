# 🦜 Parrot Trips App — Roadmap

---

## ✅ Feito

| Item | Descrição |
|---|---|
| Autenticação WhatsApp OTP | Login via código no WhatsApp, JWT, logout funcionando |
| Pipeline de conteúdo (Sheets → Supabase) | Planilha única centralizada, import por viagem ou todas de uma vez |
| Barra de progresso pré-trip | Começa em 0%, avança ao marcar fases, regressa ao desmarcar |
| Barra de progresso in-trip | Automática por data — avança conforme os dias da viagem passam |
| Deploy na GCP | Backend no Cloud Run, frontend no Cloud Storage, Makefile para deploys rápidos |
| Roteiro interativo | Fases, checklist, links úteis e atividades com tipo, horário e descrição |
| Perfil do viajante | Dados pessoais, passaporte, saúde, pagamento, seletor de data melhorado |
| UX fixes (pós-teste) | Tela inicial corrigida, botão de logout, remoção de botão desnecessário no roteiro |
| Viagem de teste configurada | 7 viajantes cadastrados, conteúdo em inglês, pronta para demos |

---

## 🔧 Próximos

| Item | Prioridade | Descrição |
|---|---|---|
| Verificar conta WhatsApp Business | 🔴 Alta | Confirmar titularidade da conta que envia os OTPs de autenticação |
| Teste no celular | 🔴 Alta | Verificar comportamento do app em dispositivos reais (iOS/Android) |
| Conferir links do app | 🟡 Média | Add-ons no perfil e Useful Links nos cards de viagem apontam para URLs corretas? |
| Usuários de teste com perfil pré-preenchido | 🟡 Média | Criar usuários de teste já com My Profile populado para demos mais fluidas |

---

## 💡 Futuro

| Item | Descrição |
|---|---|
| Interface de admin | Editar conteúdo das viagens direto no app, sem precisar de planilha ou script |
| Domínio customizado | Substituir URL atual por algo como app.parrottrips.com |
