# 🦜 Parrot Trips App — Roadmap

---

## 🔧 Para lançar para os viajantes

### App do viajante

| Item | Prioridade | Descrição |
|---|---|---|
| Campo Ideal Pace no pre-trip | 🔴 Alta | Viajante registra seu ritmo preferido de viagem durante a fase de pré-trip |
| Verificar conta WhatsApp Business | 🔴 Alta | Confirmar titularidade da conta que envia os OTPs de autenticação |
| Teste no celular (iOS/Android) | 🔴 Alta | Verificar comportamento do app em dispositivos reais |
| Conferir links do app | 🟡 Média | Links de add-ons no perfil e Useful Links nos cards apontam para URLs corretas? |
| Usuários com perfil pré-preenchido | 🟡 Média | Criar usuários de teste com My Profile populado para demos mais fluidas |

### App do staff

| Item | Prioridade | Descrição |
|---|---|---|
| Tela in-trip do staff | 🔴 Alta | Cards por dia com o que o staff precisa fazer — mesmo design do in-trip do viajante, sem ideal pace e sem dados de cadastro |
| Acesso por papel (role=staff) | 🔴 Alta | Staff autenticado entra diretamente na visão de staff, sem pré-trip |
| Switch staff ↔ viajante | 🔴 Alta | Botão que alterna entre a visão de staff e a visão do viajante — para o staff conferir o que está escrito para o viajante |
| Controle de presença dos viajantes | 🔴 Alta | Staff precisa registrar quais viajantes estão em cada etapa da viagem. Hoje é feito via QR Code — precisamos revisar se mantemos esse modelo e implementar no app |
| Conteúdo staff nos cards | 🟡 Média | Planilha e pipeline suportam campo de "staff notes" por dia/fase |

---

## 🔭 Teste interno com equipe Parrot

| Item | Prioridade | Descrição |
|---|---|---|
| Cadastrar equipe Parrot como viajantes | 🔴 Alta | Membros da Parrot entram na TEST-2026-FULL como role=traveler e percorrem a jornada completa: cadastro, checklist, ideal pace, simulação dos dias |
| Cadastrar equipe Parrot como staff | 🔴 Alta | Membros da Parrot entram na mesma viagem como role=staff e validam a visão de staff, o switch staff ↔ viajante e o controle de presença |
| Coletar feedback de UX | 🟡 Média | Identificar pontos de atrito antes de abrir para viajantes reais |

---

## ⚙️ Infraestrutura / operação

| Item | Prioridade | Descrição |
|---|---|---|
| Seleção da viagem ativa por data | 🔴 Alta | Hoje o app carrega sempre a viagem mais antiga do usuário. Precisa carregar a viagem atual (end_date >= hoje), para que um staff/viajante que participou de múltiplas viagens caia sempre na viagem certa |
| Limpeza de viagens encerradas | 🟡 Média | Script ou processo para arquivar/remover dados de viagens antigas do banco — evita acúmulo e confusão. O menu da planilha já filtra por end_date >= hoje, mas os dados permanecem no banco |

---

## 💡 Futuro

| Item | Descrição |
|---|---|
| Domínio customizado | Substituir URL atual por algo como app.parrottrips.com |
| Interface de admin | Editar conteúdo das viagens direto no app, sem precisar de planilha ou script |
