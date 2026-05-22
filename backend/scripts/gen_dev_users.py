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
from datetime import UTC, date, datetime, timedelta
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
        # asyncpg may return date as a date object or as a string "YYYY-MM-DD"
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                start_date = None
        if start_date:
            date_str = start_date.strftime("%-d %b %Y")
            label = f"{short_title} · {date_str}"
        else:
            label = short_title
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
