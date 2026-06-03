# 🦜 Parrot Trips App — Roadmap

---

## ✅ Feito

| Item | Descrição |
|---|---|
| Autenticação WhatsApp OTP | Login via código no WhatsApp, JWT, logout funcionando |
| Pipeline de conteúdo (Sheets → Supabase) | Planilha única centralizada, import por viagem |
| Barra de progresso pré-trip | Começa em 0%, avança ao marcar fases, regressa ao desmarcar |
| Barra de progresso in-trip | Automática por data — avança conforme os dias da viagem passam |
| Deploy (Cloud Run + Netlify) | Backend no Cloud Run, frontend no Netlify, Makefile para deploys rápidos |
| Roteiro interativo | Fases, checklist, links úteis e atividades com tipo, horário e descrição |
| Perfil do viajante | Dados pessoais, passaporte, saúde, pagamento, seletor de data melhorado |
| Viagem de teste configurada | 7 viajantes cadastrados, conteúdo em inglês, pronta para demos |
| Menu admin na planilha | Iniciar viagem, reset para testes, import de conteúdo via Google Sheets |

---

## 🔧 Para lançar para os viajantes

### App do viajante

| Item | Prioridade | Descrição |
|---|---|---|
| Campo Ideal Pace no pre-trip | 🔴 Alta | Viajante registra seu ritmo preferido de viagem durante a fase de pré-trip (campo no perfil ou numa fase específica) |
| Verificar conta WhatsApp Business | 🔴 Alta | Confirmar titularidade da conta que envia os OTPs de autenticação |
| Teste no celular (iOS/Android) | 🔴 Alta | Verificar comportamento do app em dispositivos reais |
| Conferir links do app | 🟡 Média | Links de add-ons no perfil e Useful Links nos cards apontam para URLs corretas? |
| Usuários de teste com perfil pré-preenchido | 🟡 Média | Criar usuários de teste com My Profile populado para demos mais fluidas |

### App do staff (visão da viagem)

| Item | Prioridade | Descrição |
|---|---|---|
| Tela in-trip do staff | 🔴 Alta | Staff vê a viagem como viajante veria: cards por dia, ao clicar vê o que o staff precisa fazer naquele dia |
| Acesso por papel (role=staff) | 🔴 Alta | Staff autenticado na viagem entra diretamente na visão de staff (sem pré-trip, sem ideal pace, sem dados de cadastro) |
| Conteúdo staff nos cards | 🟡 Média | Planilha e pipeline de conteúdo suportam campo de "staff notes" por dia/fase |

---

## 🔭 Teste interno com equipe Parrot

| Item | Prioridade | Descrição |
|---|---|---|
| Cadastrar equipe Parrot na viagem de teste | 🔴 Alta | Staff da Parrot entra na viagem TEST-2026-FULL como role=staff |
| Validar fluxo completo (pré-trip → in-trip) | 🔴 Alta | Equipe percorre toda a jornada: cadastro, checklist, ideal pace, simulação dos dias |
| Coletar feedback de UX | 🟡 Média | Identificar pontos de atrito antes de abrir para viajantes reais |

---

## 💡 Futuro

| Item | Descrição |
|---|---|
| Domínio customizado | Substituir URL atual por algo como app.parrottrips.com |
| Interface de admin | Editar conteúdo das viagens direto no app, sem precisar de planilha ou script |
