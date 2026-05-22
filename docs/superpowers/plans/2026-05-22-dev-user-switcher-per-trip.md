# Dev User Switcher — Usuário de Teste por Viagem — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar a geração de usuários de teste do seed de fases, criar um usuário de teste por viagem, e mostrar o botão 🛠️ apenas para staff.

**Architecture:** Novo script `gen_dev_users.py` lê todas as viagens do banco e escreve `devUsers.ts` diretamente. O `seed_placeholder_trip.py` perde a seção de usuários. O `DevUserSwitcher` passa a exibir o nome da viagem e só aparece quando `role === 'staff'`.

**Tech Stack:** Python 3.13, asyncpg, python-jose, React, TypeScript, Vite (`import.meta.glob`)

---

## Arquivos afetados

| Arquivo | Ação |
|---------|------|
| `backend/scripts/gen_dev_users.py` | Criar |
| `backend/scripts/seed_placeholder_trip.py` | Modificar — remover seção de usuários (linhas 342–537) |
| `frontend/src/features/dev/DevUserSwitcher.tsx` | Modificar — visibilidade staff-only + label + hasData |
| `frontend/src/config/devUsers.example.ts` | Modificar — atualizar estrutura de exemplo |
| `frontend/src/config/devUsers.ts` | Gerado pelo script (gitignored) |

---

## Task 1: Remover seção de usuários do seed_placeholder_trip.py

**Files:**
- Modify: `backend/scripts/seed_placeholder_trip.py`

- [ ] **Passo 1: Remover a constante TEST_USERS**

Em `backend/scripts/seed_placeholder_trip.py`, apagar as linhas 342–345:

```python
# REMOVER este bloco:
TEST_USERS = [
    {"phone": "+15550000001", "full_name": "Test Traveler 1"},
    {"phone": "+15550000002", "full_name": "Test Traveler 2"},
]
```

- [ ] **Passo 2: Remover o bloco de criação de usuários dentro de `seed()`**

Dentro da função `seed()`, apagar o bloco que começa em `print("Criando usuários de teste...")` e vai até o `print()` final antes do `finally`. O bloco completo a remover é:

```python
            print("Criando usuários de teste...")
            dev_users = []
            for test_user in TEST_USERS:
                existing = await conn.fetchrow(
                    "SELECT id, full_name, role FROM users WHERE phone = $1", test_user["phone"]
                )
                if existing:
                    user_id = str(existing["id"])
                    name = existing["full_name"]
                    role = existing["role"]
                    print(f"  Usuário existente: {test_user['phone']} (id={user_id})")
                else:
                    user_id = str(uuid.uuid4())
                    name = test_user["full_name"]
                    role = "traveler"
                    await conn.execute(
                        """
                        INSERT INTO users (id, phone, full_name, status, role, created_at, updated_at)
                        VALUES ($1,$2,$3,$4,$5,now(),now())
                        """,
                        user_id, test_user["phone"], name, "active", role,
                    )
                    print(f"  Usuário criado: {test_user['phone']} (id={user_id})")

                # Vincular ao trip (upsert)
                existing_tt = await conn.fetchrow(
                    "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid=$1 AND user_id=$2::uuid",
                    trip_uuid, user_id,
                )
                if not existing_tt:
                    await conn.execute(
                        """
                        INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id, created_at, updated_at)
                        VALUES ($1,$2,$3::uuid,now(),now())
                        """,
                        str(uuid.uuid4()), trip_uuid, user_id,
                    )

                token = _create_jwt(user_id, test_user["phone"], role)
                dev_users.append({
                    "userId": user_id,
                    "phone": test_user["phone"],
                    "name": name,
                    "token": token,
                    "role": role,
                })
```

- [ ] **Passo 3: Remover a impressão de devUsers.ts do summary**

Ainda dentro de `seed()`, no bloco de summary após `async with conn.transaction()`, remover:

```python
        print(f"   Usuários de teste: {len(dev_users)}")

        print("\n─────────────────────────────────────────────────────────────")
        print("Salve o conteúdo abaixo em: frontend/src/config/devUsers.ts")
        print("(esse arquivo deve estar no .gitignore)")
        print("─────────────────────────────────────────────────────────────")
        print()
        lines = ["import type { AuthUser } from '../app/providers/auth-context';", ""]
        lines.append("export const devUsers: AuthUser[] = [")
        for u in dev_users:
            lines.append(f"  {{")
            lines.append(f"    userId: '{u['userId']}',")
            lines.append(f"    phone: '{u['phone']}',")
            lines.append(f"    name: '{u['name']}',")
            lines.append(f"    token: '{u['token']}',")
            lines.append(f"    role: '{u['role']}',")
            lines.append(f"  }},")
        lines.append("];")
        print("\n".join(lines))
        print()
```

- [ ] **Passo 4: Remover import não mais usado**

Verificar se `json` ainda é usado. Se não, remover `import json` do topo do arquivo.

- [ ] **Passo 5: Atualizar docstring do arquivo**

Trocar o cabeçalho do arquivo de:

```python
"""
Seed script: popula trip_phases, checklist_items, links e activities com dados placeholder.

Uso:
  python backend/scripts/seed_placeholder_trip.py \
      --trip-uuid <wetravel_trip_uuid> \
      --start-date 2026-02-27

O script é idempotente: apaga os dados existentes para o trip_uuid antes de inserir.
Também cria 2 usuários de teste e imprime o JSON para salvar em frontend/src/config/devUsers.ts.
"""
```

por:

```python
"""
Seed script: popula trip_phases, checklist_items, links e activities com dados placeholder.

Uso:
  python backend/scripts/seed_placeholder_trip.py \
      --trip-uuid <wetravel_trip_uuid> \
      --start-date 2026-02-27

O script é idempotente: apaga os dados existentes para o trip_uuid antes de inserir.
Para criar usuários de teste, use: python backend/scripts/gen_dev_users.py
"""
```

- [ ] **Passo 6: Verificar que o script ainda roda**

```bash
cd backend
env/bin/python3 scripts/seed_placeholder_trip.py --help
```

Saída esperada: exibe `--trip-uuid` e `--start-date`, sem erros.

- [ ] **Passo 7: Commit**

```bash
git add backend/scripts/seed_placeholder_trip.py
git commit -m "refactor: remove user creation from seed_placeholder_trip"
```

---

## Task 2: Criar gen_dev_users.py

**Files:**
- Create: `backend/scripts/gen_dev_users.py`

- [ ] **Passo 1: Criar o arquivo**

Criar `backend/scripts/gen_dev_users.py` com o conteúdo completo abaixo:

```python
"""
Gera frontend/src/config/devUsers.ts com um usuário de teste por viagem cadastrada no banco.

Uso:
  cd backend
  env/bin/python3 scripts/gen_dev_users.py

Sem argumentos. Lê todas as viagens de wetravel_trips, cria/reutiliza um usuário de teste
por viagem, e escreve diretamente em frontend/src/config/devUsers.ts (gitignored).
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv
from jose import jwt

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips")
PG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30

FRONTEND_DEV_USERS_PATH = Path(__file__).parent.parent.parent / "frontend" / "src" / "config" / "devUsers.ts"


def _create_jwt(user_id: str, phone: str, role: str = "traveler") -> str:
    expire = datetime.now(UTC) + timedelta(days=JWT_EXPIRY_DAYS)
    payload = {"sub": user_id, "phone": phone, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _build_label(title: str, start_date, has_data: bool) -> str:
    short_title = title[:22] if len(title) > 22 else title
    if start_date:
        date_str = start_date.strftime("%-d %b %Y")
        label = f"{short_title} · {date_str}"
    else:
        label = short_title
    if not has_data:
        label += " ⚠️ sem dados"
    return label


async def gen(output_path: Path) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        trips = await conn.fetch(
            "SELECT trip_uuid, title, start_date FROM wetravel_trips ORDER BY start_date NULLS LAST"
        )
        print(f"Viagens encontradas: {len(trips)}")

        dev_users = []

        for i, trip in enumerate(trips, start=1):
            trip_uuid = trip["trip_uuid"]
            title = trip["title"] or f"Viagem {i}"
            start_date = trip["start_date"]

            phone = f"+1555TEST{i:04d}"

            # Verificar se a viagem tem fases no banco
            phase_count = await conn.fetchval(
                "SELECT COUNT(*) FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            has_data = (phase_count or 0) > 0

            # Criar ou reutilizar usuário
            existing = await conn.fetchrow(
                "SELECT id, full_name FROM users WHERE phone = $1", phone
            )
            if existing:
                user_id = str(existing["id"])
                name = existing["full_name"]
                print(f"  [{i}] Usuário existente: {phone} → {title[:30]}")
            else:
                user_id = str(uuid.uuid4())
                name = f"Test Traveler — {title[:30]}"
                await conn.execute(
                    """
                    INSERT INTO users (id, phone, full_name, status, role, created_at, updated_at)
                    VALUES ($1, $2, $3, 'active', 'traveler', now(), now())
                    """,
                    user_id, phone, name,
                )
                print(f"  [{i}] Usuário criado: {phone} → {title[:30]}")

            # Vincular ao trip (upsert)
            existing_tt = await conn.fetchrow(
                "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1 AND user_id = $2::uuid",
                trip_uuid, user_id,
            )
            if not existing_tt:
                await conn.execute(
                    """
                    INSERT INTO trip_travelers (id, wetravel_trip_uuid, user_id, created_at, updated_at)
                    VALUES ($1, $2, $3::uuid, now(), now())
                    """,
                    str(uuid.uuid4()), trip_uuid, user_id,
                )

            token = _create_jwt(user_id, phone)
            label = _build_label(title, start_date, has_data)

            dev_users.append({
                "userId": user_id,
                "phone": phone,
                "name": name,
                "token": token,
                "role": "traveler",
                "label": label,
                "hasData": has_data,
            })

        # Escrever devUsers.ts
        lines = [
            "// Gerado por: python backend/scripts/gen_dev_users.py",
            "// NÃO commitar — está no .gitignore (contém tokens JWT)",
            "",
            "export const devUsers = [",
        ]
        for u in dev_users:
            has_data_str = "true" if u["hasData"] else "false"
            lines += [
                "  {",
                f"    userId: '{u['userId']}',",
                f"    phone: '{u['phone']}',",
                f"    name: '{u['name']}',",
                f"    token: '{u['token']}',",
                f"    role: 'traveler' as const,",
                f"    label: '{u['label']}',",
                f"    hasData: {has_data_str},",
                "  },",
            ]
        lines.append("] as const;")
        lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

        print(f"\n✅ Gerado: {output_path}")
        print(f"   {len(dev_users)} usuário(s) de teste")
        for u in dev_users:
            status = "✓ com dados" if u["hasData"] else "⚠ sem dados"
            print(f"   {u['label'][:40]:<40} {status}")

    finally:
        await conn.close()


if __name__ == "__main__":
    if not JWT_SECRET:
        print("Aviso: JWT_SECRET não configurado. Os tokens gerados serão inválidos.")
    asyncio.run(gen(FRONTEND_DEV_USERS_PATH))
```

- [ ] **Passo 2: Rodar o script e verificar saída**

```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

Saída esperada (exemplo com 3 viagens):
```
Viagens encontradas: 3
  [1] Usuário criado: +1555TEST0001 → Wharton Brazil Trek December 2026
  [2] Usuário criado: +1555TEST0002 → UCLA Carnival 27 Trek
  [3] Usuário criado: +1555TEST0003 → HBS Diaspora Brazil Trek

✅ Gerado: .../frontend/src/config/devUsers.ts
   3 usuário(s) de teste
   Wharton 2026 · 8 Dec 2026            ✓ com dados
   UCLA 2027 · 5 Feb 2027               ⚠ sem dados
   HBS Diaspora Brazil Trek · 15 Jan    ⚠ sem dados
```

- [ ] **Passo 3: Verificar o arquivo gerado**

```bash
cat frontend/src/config/devUsers.ts
```

O arquivo deve ter 3 entradas com `label`, `hasData`, e `role: 'traveler' as const`.

- [ ] **Passo 4: Rodar o script uma segunda vez (verificar idempotência)**

```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

Saída esperada: "Usuário **existente**" para todos (não "criado"). O arquivo deve ter o mesmo conteúdo (exceto tokens novos com nova expiração).

- [ ] **Passo 5: Commit**

```bash
git add backend/scripts/gen_dev_users.py
git commit -m "feat: add gen_dev_users script — one test user per trip"
```

---

## Task 3: Atualizar DevUserSwitcher.tsx

**Files:**
- Modify: `frontend/src/features/dev/DevUserSwitcher.tsx`

- [ ] **Passo 1: Substituir o conteúdo completo do arquivo**

Substituir `frontend/src/features/dev/DevUserSwitcher.tsx` pelo seguinte:

```tsx
import { useState } from 'react';
import { useAuth } from '../../app/providers/auth-context';

type DevUser = {
  userId: string;
  phone: string;
  name: string;
  token: string;
  role: 'traveler' | 'staff';
  label: string;
  hasData: boolean;
};

// devUsers.ts é gerado por gen_dev_users.py e está no .gitignore
// import.meta.glob retorna {} se o arquivo não existir — graceful fallback
const devModules = import.meta.glob<{ devUsers: readonly DevUser[] }>(
  '../../config/devUsers.ts',
  { eager: true }
);
const devUsers: DevUser[] = [...(Object.values(devModules)[0]?.devUsers ?? [])];

export default function DevUserSwitcher() {
  const [open, setOpen] = useState(false);
  const { user, login } = useAuth();

  // Só aparece em dev, com usuários carregados, e quando staff está logado
  if (!import.meta.env.DEV || devUsers.length === 0 || user?.role !== 'staff') return null;

  const handleSelect = (u: DevUser) => {
    login(u.userId, u.phone, u.name, u.token, u.role);
    setOpen(false);
    window.location.reload();
  };

  return (
    <div className="fixed bottom-24 right-4 z-50">
      {open && (
        <div className="mb-2 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden w-64">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Ver como viajante</p>
          </div>
          {devUsers.map(u => (
            <button
              key={u.userId}
              onClick={() => handleSelect(u)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
            >
              <p className="text-sm font-semibold text-gray-800">{u.label}</p>
              {!u.hasData && (
                <p className="text-xs text-amber-500 mt-0.5">sem dados — testa estado vazio</p>
              )}
            </button>
          ))}
        </div>
      )}
      <button
        onClick={() => setOpen(!open)}
        className="w-12 h-12 bg-gray-800 text-white rounded-full shadow-lg flex items-center justify-center text-lg hover:bg-gray-700 transition-colors"
        title="Ver como viajante"
      >
        👁️
      </button>
    </div>
  );
}
```

Nota: o ícone foi trocado de 🛠️ para 👁️ para refletir melhor a ação ("ver como viajante").

- [ ] **Passo 2: Verificar no browser que o botão aparece na tela de staff**

Abrir `http://localhost:5173`, entrar com o número de staff. O botão 👁️ deve aparecer no canto inferior direito.

- [ ] **Passo 3: Verificar que o botão NÃO aparece para viajante**

Clicar no botão, selecionar uma viagem com dados. O app recarrega como viajante. O botão 👁️ **não deve aparecer** na tela do viajante.

- [ ] **Passo 4: Verificar viagem sem dados**

Voltar para staff (recarregar e fazer login com número de staff). Clicar no botão, selecionar uma viagem marcada como "sem dados". Confirmar que a tela de viajante mostra o estado de erro/vazio sem quebrar o app.

- [ ] **Passo 5: Commit**

```bash
git add frontend/src/features/dev/DevUserSwitcher.tsx
git commit -m "feat: show dev switcher only for staff, display trip label per entry"
```

---

## Task 4: Atualizar devUsers.example.ts

**Files:**
- Modify: `frontend/src/config/devUsers.example.ts`

- [ ] **Passo 1: Substituir o conteúdo do arquivo de exemplo**

Substituir `frontend/src/config/devUsers.example.ts` pelo seguinte:

```ts
// Exemplo de estrutura do devUsers.ts gerado por: python backend/scripts/gen_dev_users.py
// O arquivo real (devUsers.ts) está no .gitignore — nunca commitar (contém tokens JWT).

export const devUsers = [
  {
    userId: 'uuid-do-usuario',
    phone: '+1555TEST0001',
    name: 'Test Traveler — Nome da Viagem',
    token: 'jwt-token-gerado-pelo-script',
    role: 'traveler' as const,
    label: 'Nome da Viagem · 8 Dec 2026',   // exibido no switcher
    hasData: true,                             // false se trip_phases vazio
  },
] as const;
```

- [ ] **Passo 2: Commit**

```bash
git add frontend/src/config/devUsers.example.ts
git commit -m "docs: update devUsers.example.ts with new label and hasData fields"
```

---

## Self-Review

**Spec coverage:**
- ✅ Script separado `gen_dev_users.py` — Task 2
- ✅ Seed script perde seção de usuários — Task 1
- ✅ Um usuário de teste por viagem — Task 2
- ✅ Label com nome da viagem — Tasks 2 e 3
- ✅ Indicador visual para viagens sem dados — Task 3
- ✅ Botão só para staff — Task 3
- ✅ Escreve devUsers.ts diretamente (sem copiar) — Task 2
- ✅ devUsers.example.ts atualizado — Task 4

**Placeholder scan:** Nenhum TBD ou TODO. Todos os passos têm código completo.

**Type consistency:** `DevUser` definido em Task 3 com `label: string` e `hasData: boolean`. O script em Task 2 gera exatamente esses campos. `login()` recebe `(userId, phone, name, token, role)` — compatível com `AuthContextType`.
