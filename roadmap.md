# 🦜 Parrot Trips App — Roadmap

---

## Plano de ação

### Fase 1 — Desbloqueio imediato (1-2 dias)

| Item | Prioridade | Descrição |
|---|---|---|
| Seleção da viagem ativa por data | 🔴 Alta | Crítico para o staff app: o app carrega sempre a viagem mais antiga do usuário. Corrigir `GET /me/trip` para carregar a viagem com `end_date >= hoje`. Staff que guia outubro e novembro precisa disso |
| Campo Ideal Pace no pre-trip | 🔴 Alta | Viajante registra seu ritmo preferido durante o pré-trip. Backend + frontend |
| Service Agreement — inserção por viajante | 🔴 Alta | Backend e banco já existem, frontend já exibe o link. Falta: forma de popular a URL por viajante (campo na planilha ou tela de admin) |
| ~~Verificar conta WhatsApp Business~~ | ✅ Resolvido | Perfil da conta ajustado no Meta Business Manager |

### Fase 2 — Teste interno como viajante

Com ideal pace pronto e WhatsApp confirmado, equipe Parrot percorre o fluxo completo como `role=traveler`: cadastro, checklist, ideal pace, simulação dos dias in-trip. O feedback dessa rodada orienta ajustes antes de construir o app do staff.

| Item | Prioridade | Descrição |
|---|---|---|
| Cadastrar equipe Parrot como viajantes | 🔴 Alta | Membros da Parrot entram na TEST-2026-FULL como role=traveler |
| Conferir links do app | 🟡 Média | Links de add-ons no perfil e Useful Links nos cards apontam para URLs corretas? |
| Usuários com perfil pré-preenchido | 🟡 Média | Criar usuários de teste com My Profile populado para demos mais fluidas |
| Coletar feedback de UX | 🟡 Média | Identificar pontos de atrito antes de abrir para viajantes reais |

### Fase 3 — App do staff (≈ 1 semana)

Construir nesta ordem — cada item desbloqueia o próximo:

| Ordem | Item | Descrição |
|---|---|---|
| 1 | Acesso por papel (role=staff) | Staff autenticado entra diretamente na visão de staff, sem pré-trip |
| 2 | Tela in-trip do staff | Cards por dia com o que o staff precisa fazer — mesmo design do in-trip do viajante, sem ideal pace e sem dados de cadastro |
| 3 | Switch staff ↔ viajante | Botão que alterna entre a visão de staff e a visão do viajante — para o staff conferir o que está escrito para o viajante |
| 4 | Conteúdo staff nos cards | Planilha e pipeline suportam campo de "staff notes" por dia/fase |
| 5 | Controle de presença | **Depende de decisão de design** — hoje é feito via QR Code. Revisar se mantemos esse modelo antes de implementar. Discutir durante a Fase 2 |

### Fase 4 — Teste interno como staff

| Item | Descrição |
|---|---|
| Cadastrar equipe Parrot como staff | Membros da Parrot entram na TEST-2026-FULL como role=staff |
| Validar visão de staff | Conferir tela in-trip, switch staff ↔ viajante e controle de presença |
| Coletar feedback de UX | Segunda rodada de feedback antes de abrir para viajantes reais |

### Fase 5 — Refinamento e operação

| Item | Prioridade | Descrição |
|---|---|---|
| Limpeza de viagens encerradas | 🟡 Média | Script para arquivar/remover dados de viagens antigas — evita acúmulo e confusão |

---

## 💡 Futuro

| Item | Descrição |
|---|---|
| Domínio customizado | Substituir URL atual por algo como app.parrottrips.com |
| Interface de admin | Editar conteúdo das viagens direto no app, sem precisar de planilha ou script |
