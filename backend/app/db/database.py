"""Database helpers and schema initialization for the application."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.core.config import get_database_path

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS checklist_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id TEXT NOT NULL,
        phase_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, trip_id, phase_id, item_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS phase_completion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id TEXT NOT NULL,
        phase_id TEXT NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, trip_id, phase_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        trip_id TEXT NOT NULL DEFAULT 'ross26',
        preferred_name TEXT,
        email TEXT,
        dob TEXT,
        gender TEXT,
        transfer_platform TEXT,
        package_option TEXT,
        num_people INTEGER,
        usd_amount REAL,
        proof_of_transfer TEXT,
        dietary_restrictions_yn TEXT,
        dietary_restrictions_desc TEXT,
        seasickness_yn TEXT,
        first_name_passport TEXT,
        last_name_passport TEXT,
        passport_country TEXT,
        passport_number TEXT,
        passport_issue_date TEXT,
        passport_expiration_date TEXT,
        plus_one_yn TEXT,
        plus_one_name TEXT,
        plus_one_email TEXT,
        intl_flights_help_yn TEXT,
        intl_flights_help_details TEXT,
        travel_insurance_help_yn TEXT,
        unforgettable_trip_details TEXT,
        receive_addon_updates TEXT,
        esim_qr_image TEXT,
        roommate_user_id INTEGER,
        arrival_date TEXT,
        arrival_time TEXT,
        arrival_flight TEXT,
        departure_date TEXT,
        departure_time TEXT,
        departure_flight TEXT,
        service_agreement_url TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (roommate_user_id) REFERENCES users(id)
    )
    """,
]


def connect_to_database(database_path: str | Path | None = None) -> aiosqlite.Connection:
    """Open an aiosqlite connection for the configured database path."""
    resolved_path = str(database_path or get_database_path())
    return aiosqlite.connect(resolved_path)


async def init_db(database_path: str | Path | None = None) -> None:
    """Create the tables required by the active application scope."""
    resolved_path = Path(str(database_path or get_database_path()))
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    async with connect_to_database(resolved_path) as db:
        for statement in SCHEMA_STATEMENTS:
            await db.execute(statement)

        await db.commit()
