"""Database helpers and schema initialization for the application."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from app.core.config import get_database_path

DEFAULT_MISSIONS = [
    (
        "ross26",
        "First Photo!",
        "Upload your first photo to the group album",
        50,
        "📸",
        "social",
        1,
    ),
    (
        "ross26",
        "Social Butterfly",
        "Comment on 3 different activities",
        100,
        "🦋",
        "social",
        2,
    ),
    (
        "ross26",
        "Early Bird",
        "Complete all your registration details before the trip",
        200,
        "🐦",
        "preparation",
        3,
    ),
    (
        "ross26",
        "Adventure Seeker",
        "Join at least 2 optional activities",
        150,
        "🏄",
        "adventure",
        4,
    ),
    (
        "ross26",
        "Memory Maker",
        "Share 10 photos across the trip",
        300,
        "🌟",
        "social",
        5,
    ),
    (
        "ross26",
        "Group Leader",
        "Help 3 travelers with their preparation",
        250,
        "👑",
        "social",
        6,
    ),
    (
        "ross26",
        "Beach Explorer",
        "Visit 3 different beaches during the trip",
        150,
        "🏖️",
        "adventure",
        7,
    ),
    (
        "ross26",
        "Foodie Tour",
        "Try food at 5 different local restaurants",
        200,
        "🍽️",
        "adventure",
        8,
    ),
    (
        "ross26",
        "Culture Vulture",
        "Visit Cristo Redentor and Pão de Açúcar",
        175,
        "🏛️",
        "adventure",
        9,
    ),
    (
        "ross26",
        "Night Owl",
        "Attend 3 evening events or nightlife activities",
        200,
        "🦉",
        "adventure",
        10,
    ),
    (
        "ross26",
        "Island Life",
        "Complete all Ilha Grande activities",
        250,
        "🏝️",
        "adventure",
        11,
    ),
    (
        "ross26",
        "Samba Spirit",
        "Dance samba at a local venue",
        100,
        "💃",
        "culture",
        12,
    ),
]

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
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id TEXT NOT NULL,
        phase_id TEXT NOT NULL,
        text TEXT NOT NULL,
        is_private BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
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
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_id TEXT NOT NULL DEFAULT 'ross26',
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'info',
        link TEXT,
        read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
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
    """
    CREATE TABLE IF NOT EXISTS missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id TEXT NOT NULL DEFAULT 'ross26',
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        points INTEGER NOT NULL DEFAULT 50,
        icon TEXT DEFAULT '🎯',
        category TEXT DEFAULT 'general',
        sort_order INTEGER DEFAULT 0,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mission_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mission_id INTEGER NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (mission_id) REFERENCES missions(id),
        UNIQUE(user_id, mission_id)
    )
    """,
]


def connect_to_database(database_path: str | Path | None = None) -> aiosqlite.Connection:
    """Open an aiosqlite connection for the configured database path."""
    resolved_path = str(database_path or get_database_path())
    return aiosqlite.connect(resolved_path)


async def init_db(database_path: str | Path | None = None) -> None:
    """Create required tables and seed default missions when the database is empty."""
    resolved_path = Path(str(database_path or get_database_path()))
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    async with connect_to_database(resolved_path) as db:
        for statement in SCHEMA_STATEMENTS:
            await db.execute(statement)

        cursor = await db.execute("SELECT COUNT(*) FROM missions")
        mission_count = (await cursor.fetchone())[0]
        if mission_count == 0:
            await db.executemany(
                """
                INSERT INTO missions (
                    trip_id, title, description, points, icon, category, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                DEFAULT_MISSIONS,
            )

        await db.commit()
