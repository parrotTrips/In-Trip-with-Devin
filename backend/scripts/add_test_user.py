"""
Cadastrar um usuário de teste e vinculá-lo a uma viagem.

Útil para demos e testes com pessoas externas — cadastra o número de WhatsApp
no banco e vincula o usuário à viagem especificada.

Usage:
  cd backend
  poetry run python scripts/add_test_user.py \
    --phone +5511999999999 \
    --name "Nome da Pessoa" \
    --trip-uuid TEST-2026-FULL

  # Dry run (mostra o que seria feito sem executar):
  poetry run python scripts/add_test_user.py \
    --phone +5511999999999 \
    --name "Nome da Pessoa" \
    --trip-uuid TEST-2026-FULL \
    --dry-run

  # Remover usuário e vínculo (desfazer):
  poetry run python scripts/add_test_user.py \
    --phone +5511999999999 \
    --remove
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips",
)
PG_URL = (
    DATABASE_URL
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("postgresql+psycopg2://", "postgresql://")
)


async def add_user(phone: str, name: str, trip_uuid: str, dry_run: bool) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        # Verificar se a viagem existe
        trip = await conn.fetchrow(
            "SELECT trip_uuid, title FROM wetravel_trips WHERE trip_uuid = $1", trip_uuid
        )
        if not trip:
            print(f"Viagem '{trip_uuid}' não encontrada no banco.")
            return

        print(f"Viagem: {trip['title']} ({trip_uuid})")

        # Verificar se usuário já existe
        existing_user = await conn.fetchrow(
            "SELECT id, full_name FROM users WHERE phone = $1", phone
        )
        if existing_user:
            print(f"Usuário já existe: {existing_user['full_name']} ({phone})")
            user_id = existing_user["id"]
        else:
            print(f"Novo usuário: {name} ({phone})")
            user_id = None

        # Verificar se já está vinculado à viagem
        if existing_user:
            existing_link = await conn.fetchrow(
                "SELECT id FROM trip_travelers WHERE user_id = $1 AND wetravel_trip_uuid = $2",
                existing_user["id"], trip_uuid,
            )
            if existing_link:
                print(f"Usuário já está vinculado à viagem '{trip_uuid}'.")
                return

        if dry_run:
            print("\nDry run — nada foi alterado.")
            return

        async with conn.transaction():
            if not existing_user:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (phone, full_name, status, role)
                    VALUES ($1, $2, 'active', 'traveler')
                    RETURNING id
                    """,
                    phone, name,
                )
                user_id = row["id"]
                print(f"Usuário criado com ID: {user_id}")

            await conn.execute(
                """
                INSERT INTO trip_travelers (wetravel_trip_uuid, user_id)
                VALUES ($1, $2)
                """,
                trip_uuid, user_id,
            )
            print(f"Usuário vinculado à viagem '{trip_uuid}'.")

        print(f"\nPronto! {name} pode acessar o app com o número {phone}.")
    finally:
        await conn.close()


async def remove_user(phone: str) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        user = await conn.fetchrow(
            "SELECT id, full_name FROM users WHERE phone = $1", phone
        )
        if not user:
            print(f"Usuário com telefone {phone} não encontrado.")
            return

        print(f"Removendo: {user['full_name']} ({phone})")

        confirm = input("Confirmar remoção? [y/N] ").strip().lower()
        if confirm != "y":
            print("Abortado.")
            return

        async with conn.transaction():
            tt_rows = await conn.fetch(
                "SELECT id FROM trip_travelers WHERE user_id = $1", user["id"]
            )
            if tt_rows:
                tt_ids = [str(r["id"]) for r in tt_rows]
                await conn.execute(
                    "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])",
                    tt_ids,
                )
                await conn.execute(
                    "DELETE FROM trip_travelers WHERE user_id = $1", user["id"]
                )
            await conn.execute("DELETE FROM users WHERE id = $1", user["id"])

        print(f"Usuário removido.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cadastrar usuário de teste em uma viagem")
    parser.add_argument("--phone", required=True, help="Número de WhatsApp com DDI (+5511...)")
    parser.add_argument("--name", help="Nome completo (obrigatório para novo usuário)")
    parser.add_argument("--trip-uuid", help="UUID da viagem (ex: TEST-2026-FULL)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que seria feito sem executar")
    parser.add_argument("--remove", action="store_true", help="Remover o usuário e seus vínculos")
    args = parser.parse_args()

    if args.remove:
        asyncio.run(remove_user(args.phone))
    else:
        if not args.name:
            parser.error("--name é obrigatório para cadastrar um usuário")
        if not args.trip_uuid:
            parser.error("--trip-uuid é obrigatório para cadastrar um usuário")
        asyncio.run(add_user(args.phone, args.name, args.trip_uuid, args.dry_run))
