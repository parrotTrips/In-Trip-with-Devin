# 🦜 Parrot Trips App — Roadmap

---

## Plano de ação

### Fase 1 — Fundação técnica

Correções e funcionalidades que precisam estar prontas antes de qualquer teste com pessoas.

| Item | Status | Descrição |
|---|---|---|
| Seleção da viagem ativa por data | ✅ Feito | `GET /me/trip` filtra `end_date >= hoje` — staff com múltiplas viagens cai sempre na correta |
| Service Agreement por viagem | ✅ Feito | Campo em `wetravel_trips`, exposto no `GET /me/trip`, populado via planilha (aba Viagens) |
| Campo Ideal Pace no pre-trip | ✅ Feito | Parrot no card correto vindo do banco, coluna `ideal_pace` na aba Fases da planilha |

---

### Fase 2 — Teste interno como viajante

Equipe Parrot percorre o fluxo completo como `role=traveler`. Objetivo: validar a experiência do viajante e coletar feedback antes de construir o app do staff.

| Item | Descrição |
|---|---|
| Cadastrar equipe Parrot como viajantes | Membros da Parrot entram na TEST-2026-FULL como role=traveler |
| Conferir links do app | Links de add-ons no perfil e Useful Links nos cards apontam para URLs corretas? |
| Usuários com perfil pré-preenchido | Criar usuários com My Profile populado para o teste ser mais realista |
| Decidir modelo de controle de presença | Durante este teste, definir se mantemos QR Code ou outro modelo. A decisão impacta o design do staff app |
| Coletar feedback de UX | Identificar pontos de atrito antes de abrir para viajantes reais |

---

### Fase 3 — App do staff

Construir nesta ordem — cada item desbloqueia o próximo:

| Ordem | Item | Descrição |
|---|---|---|
| 1 | Acesso por papel (role=staff) | Staff autenticado entra diretamente na visão de staff, sem pré-trip, sem ideal pace, sem dados de cadastro |
| 2 | Tela in-trip do staff | Cards por dia com o que o staff precisa fazer — mesmo design do in-trip do viajante |
| 3 | Conteúdo staff nos cards | Planilha e pipeline suportam campo de "staff notes" por dia/fase |
| 4 | Switch staff ↔ viajante | Botão que alterna entre a visão de staff e a visão do viajante — para o staff conferir o que o viajante está vendo |
| 5 | Controle de presença | Implementar após decisão de design da Fase 2 (manter QR Code ou novo modelo) |

---

### Fase 4 — Teste interno como staff

Equipe Parrot percorre o fluxo como `role=staff` na mesma viagem de teste.

| Item | Descrição |
|---|---|
| Cadastrar equipe Parrot como staff | Membros da Parrot entram na TEST-2026-FULL como role=staff |
| Validar visão de staff | Conferir tela in-trip, switch staff ↔ viajante e controle de presença |
| Validar seleção de viagem ativa | Simular staff com duas viagens cadastradas para confirmar que o app carrega a correta |
| Coletar feedback de UX | Segunda rodada de feedback antes de abrir para viajantes reais |

---

### Fase 5 — Operação contínua

| Item | Descrição |
|---|---|
| Limpeza de viagens encerradas | Script para arquivar/remover dados de viagens antigas — evita acúmulo conforme o número de viagens cresce |

---

## 💡 Futuro

| Item | Descrição |
|---|---|
| Domínio customizado | Substituir URL atual por algo como app.parrottrips.com |
| Interface de admin | Editar conteúdo das viagens direto no app, sem precisar de planilha ou script |
