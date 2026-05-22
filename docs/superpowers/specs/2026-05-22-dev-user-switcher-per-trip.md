# Dev User Switcher — Usuário de Teste por Viagem

**Data:** 2026-05-22
**Status:** Aprovado

---

## Contexto

O `DevUserSwitcher` é um botão 🛠️ de desenvolvimento que permite ao staff alternar rapidamente para a visão de um viajante de teste sem precisar fazer login manual. Atualmente cria dois usuários fixos ("Test Traveler 1" e "Test Traveler 2") vinculados a uma única viagem, o que dificulta testar múltiplas viagens e estados vazios.

---

## Objetivo

- Ter um usuário de teste por viagem cadastrada no banco
- Conseguir ver como fica a tela para viagens sem dados (estado vazio)
- O botão 🛠️ aparecer apenas para staff logado
- Separar a geração de usuários de teste da seed de fases/atividades

---

## O que NÃO está no escopo

- Feature de "preview como viajante" para staff em produção (futuro, quando a staff area estiver estruturada)
- Alterações na autenticação real ou no fluxo de login de viajantes

---

## Design

### Novo script: `backend/scripts/gen_dev_users.py`

Script independente sem argumentos obrigatórios.

**Comportamento:**
1. Conecta ao banco e lê todas as viagens de `wetravel_trips` ordenadas por `start_date`
2. Para cada viagem, deriva um phone de teste determinístico: `+1555TEST{N:04d}` onde N é o índice (1, 2, 3...)
3. Cria ou reutiliza o usuário com esse phone em `users` (role: `traveler`)
4. Vincula o usuário à viagem em `trip_travelers` via upsert
5. Verifica se a viagem tem fases em `trip_phases` (flag `has_data`)
6. Gera JWT com validade de 30 dias
7. **Escreve diretamente** em `frontend/src/config/devUsers.ts` (sem copiar manualmente)

**Label de exibição:**
- Com dados: `"Wharton 2026 · 8 Dec"`
- Sem dados: `"UCLA 2027 · 5 Feb ⚠️ sem dados"`

Formato derivado de `wetravel_trips.title` (truncado se necessário) + `start_date`.

**Rodagem:**
```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

Sem argumentos. Sempre reflete o estado atual do banco. Idempotente.

---

### Alteração em `frontend/src/config/devUsers.ts`

O arquivo gerado usa um tipo estendido (só para o switcher, não para `AuthUser`):

```ts
export const devUsers = [
  {
    userId: string,
    phone: string,           // '+1555TEST0001'
    name: string,            // 'Test Traveler — Wharton 2026'
    token: string,           // JWT válido por 30 dias
    role: 'traveler',
    label: string,           // 'Wharton 2026 · 8 Dec'
    hasData: boolean,        // true se trip_phases existe para essa viagem
  },
  ...
]
```

`AuthUser` não muda. Os campos `label` e `hasData` são ignorados pelo AuthContext — são apenas metadados de exibição.

---

### Alteração em `frontend/src/features/dev/DevUserSwitcher.tsx`

**Visibilidade:** o componente retorna `null` se:
- Não está em `import.meta.env.DEV`, **ou**
- `devUsers` está vazio, **ou**
- `user?.role !== 'staff'` (invisível para viajantes reais e na tela de login)

**Exibição:** usa `label` em vez de `name ?? phone`. Entradas com `hasData: false` recebem um aviso visual (ícone ⚠️ ou texto em cor diferente).

**Comportamento ao selecionar:** igual ao atual — chama `login()` com os campos de `AuthUser` e faz `window.location.reload()`.

---

### `backend/scripts/seed_placeholder_trip.py`

Remove a seção de criação de usuários de teste (`TEST_USERS`, loop de criação, output de `devUsers.ts`). Fica focado exclusivamente em popular `trip_phases`, `trip_phase_checklist_items`, `trip_phase_links` e `trip_activities`.

---

## Fluxo de uso

```
1. Rodar seed de fases (se quiser dados):
   cd backend && env/bin/python3 scripts/seed_placeholder_trip.py --trip-uuid 6608858457 --start-date 2026-12-08

2. Gerar usuários de teste (sempre que o banco mudar):
   cd backend && env/bin/python3 scripts/gen_dev_users.py

3. Abrir o app como staff → botão 🛠️ aparece → selecionar viagem → ver UI do viajante
```

---

## Arquivos afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/scripts/gen_dev_users.py` | Novo |
| `backend/scripts/seed_placeholder_trip.py` | Remove seção de usuários |
| `frontend/src/features/dev/DevUserSwitcher.tsx` | Visibilidade (só staff) + label + hasData |
| `frontend/src/config/devUsers.ts` | Gerado pelo novo script |
| `frontend/src/config/devUsers.example.ts` | Atualizar estrutura de exemplo |
