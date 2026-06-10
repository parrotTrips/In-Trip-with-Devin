# Ideal Pace — Design (pendente de decisão)

Documento para discussão. Não implementar antes de alinhar as respostas abaixo.

---

## O que é

Um campo coletado durante o pré-trip em que o viajante registra seu ritmo preferido de viagem. A Parrot usa essa informação para conhecer melhor o grupo antes da viagem.

---

## Perguntas em aberto

### 1. Onde fica no app?

**Opção A — Card no game board do pre-trip**
Um card dedicado chamado "Ideal Pace" no mesmo nível das outras fases pré-trip. O viajante clica, responde e marca como completo. Fica visível na barra de progresso.

**Opção B — Seção dentro do My Profile**
Aparece como mais uma seção colapsável no perfil, junto com passaporte, restrições alimentares, etc. Não afeta a barra de progresso.

### 2. Como o viajante responde?

**Opção A — Escala numérica (1–5)**
Ex: de "Very Relaxed" a "Very Active". Simples de responder, fácil de agregar por grupo.

**Opção B — Seleção de perfis**
Ex: "Relaxed 🌴", "Balanced ⚖️", "Active 🏃", "Adventurous 🧗". Mais visual e descritivo.

**Opção C — Texto livre**
O viajante descreve com suas próprias palavras. Mais rico mas difícil de agregar.

### 3. Para que a Parrot usa?

- A Parrot usa internamente para planejar atividades do grupo?
- O viajante vê o resultado de alguma forma no app (ex: "seu grupo é 70% Balanced")?
- A resposta impacta algo no roteiro ou é apenas informativa?

### 4. É obrigatório?

- Bloqueia o avanço do pre-trip se não for preenchido?
- Ou é opcional e o viajante pode pular?

---

## Impacto técnico estimado (após decisão)

| Componente | O que muda |
|---|---|
| Banco | Novo campo `ideal_pace` em `traveler_profiles` (ou nova tabela se for escala com múltiplos eixos) |
| Backend | Campo no schema `ProfileUpdate` + retornado no `GET /profile` |
| Frontend | Novo campo na tela (card no game board ou seção no My Profile) |
| Planilha | Nenhuma — dado vem do viajante, não da equipe |

---

## Status

⏳ **Aguardando decisão de design** — discutir antes de implementar.
