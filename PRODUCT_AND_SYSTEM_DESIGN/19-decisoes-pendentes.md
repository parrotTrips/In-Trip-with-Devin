# Decisões Pendentes

Registro de tópicos que precisam ser discutidos e validados antes de implementar ou antes de ir para produção com viajantes reais.

---

## 1. Viagem ativa por data — lógica para múltiplas viagens

**Contexto:**
Hoje o `GET /me/trip` carrega a viagem com `end_date >= hoje` mais próxima. Funciona bem para o caso simples (um usuário, uma viagem ativa por vez).

**O que precisa ser validado:**
- Um staff pode estar cadastrado em duas viagens com datas sobrepostas (ex: termina de guiar uma e começa outra na mesma semana)? Se sim, qual viagem o app deve mostrar?
- O que acontece se um viajante não tiver nenhuma viagem com `end_date >= hoje`? Hoje cai na tela "sem viagem" — é o comportamento correto?
- Precisa de uma forma do usuário selecionar manualmente entre viagens disponíveis, ou sempre mostramos apenas uma?

---

## 2. Ideal Pace — coleta durante o pre-trip

**Contexto:**
Queremos coletar o ritmo preferido de viagem de cada viajante durante o pré-trip para a Parrot conhecer melhor o grupo.

**O que precisa ser decidido:**

- **Onde fica no app?** Card dedicado no game board do pre-trip, ou seção dentro do My Profile?
- **Como o viajante responde?** Escala (1–5), seleção de perfis (ex: "Relaxed 🌴 / Balanced ⚖️ / Active 🏃") ou texto livre?
- **Para que a Parrot usa?** Planejamento interno do grupo? O viajante vê algum resultado no app?
- **É obrigatório?** Bloqueia o avanço do pre-trip ou é opcional?

---

## 3. Controle de presença — modelo do QR Code

**Contexto:**
O staff precisa registrar quais viajantes estão presentes em cada atividade do dia. Hoje isso é feito fora do app via QR Code.

**O que precisa ser decidido:**
- Mantemos o QR Code? O viajante mostra o QR no celular e o staff escaneia?
- Ou invertemos: o staff mostra um QR da atividade e o viajante escaneia para fazer check-in?
- Existe algum outro modelo (lista manual, NFC, etc.) que faça mais sentido na operação real?
- Onde o QR Code do viajante vive no app? (Uma tela dedicada, dentro do perfil, na home?)

---

## 4. Switch staff ↔ viajante

**Contexto:**
O staff precisa conseguir alternar entre a visão de staff e a visão do viajante para conferir o que está escrito para o viajante.

**O que precisa ser decidido:**
- O switch mostra a visão de qualquer viajante da viagem, ou apenas a visão genérica (como se fosse um viajante sem progresso)?
- O botão de switch fica no header do staff app ou em outro lugar?

