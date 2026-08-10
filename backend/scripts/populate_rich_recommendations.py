"""Populate rich local recommendations in the Trip Content sheet and Supabase.

The script is intentionally scoped to one trip UUID. It preserves rows for
other trips, replaces this trip's recommendation rows in the sheet, then
imports the same rows into `trip_recommendations`.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import asyncpg
import google.auth
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

from scripts.import_trip_content import parse_recommendations_tab

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
TRIP_CONTENT_SHEET_ID = os.environ.get("TRIP_CONTENT_SHEET_ID", "")
SERVICE_ACCOUNT_FILE = Path(__file__).parent.parent / "secrets" / "gcp-service-account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

RECOMMENDATIONS_HEADERS = [
    "trip_uuid",
    "name",
    "description",
    "address",
    "photo_url",
    "sort_order",
    "category",
    "neighborhood",
    "location",
    "highlight",
    "price_range",
    "rating",
    "map_url",
    "emoji",
]


def build_sheets_client():
    if SERVICE_ACCOUNT_FILE.exists():
        creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=SCOPES,
        )
    else:
        creds, _ = google.auth.default(scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def curated_recommendations(trip_uuid: str) -> list[list[str]]:
    return [
        [
            trip_uuid,
            "Babbo Osteria",
            "Upscale Italian cooking in Ipanema with handmade pasta, warm service and a strong wine list. Good option for a polished dinner close to the main hotel area.",
            "Rua Barao da Torre, 632 - Ipanema, Rio de Janeiro - RJ",
            "",
            "1",
            "restaurants",
            "Ipanema",
            "rio",
            "Near the hotel",
            "$$$",
            "4.7",
            "https://maps.google.com/?q=Babbo+Osteria+Ipanema+Rio",
            "🍝",
        ],
        [
            trip_uuid,
            "Teva Bistro",
            "Creative plant-based restaurant with colorful plates, cocktails and a relaxed Ipanema atmosphere. Useful for vegan, vegetarian and lighter dinner suggestions.",
            "Av. Henrique Dumont, 110 - Ipanema, Rio de Janeiro - RJ",
            "",
            "2",
            "restaurants",
            "Ipanema",
            "rio",
            "Vegan-friendly",
            "$$",
            "4.8",
            "https://maps.google.com/?q=Teva+Bistro+Ipanema+Rio",
            "🥗",
        ],
        [
            trip_uuid,
            "CT Boucherie",
            "Classic French-Brazilian steakhouse by chef Claude Troisgros, known for premium cuts and generous side dishes served at the table.",
            "Rua Dias Ferreira, 636 - Leblon, Rio de Janeiro - RJ",
            "",
            "3",
            "restaurants",
            "Leblon",
            "rio",
            "Must-try steakhouse",
            "$$$$",
            "4.8",
            "https://maps.google.com/?q=CT+Boucherie+Leblon+Rio",
            "🥩",
        ],
        [
            trip_uuid,
            "Jobi",
            "Long-running Leblon bar and restaurant with cold chopp, casual Brazilian dishes and a lively local crowd. Good for a relaxed night after activities.",
            "Av. Ataulfo de Paiva, 1166 - Leblon, Rio de Janeiro - RJ",
            "",
            "4",
            "bars",
            "Leblon",
            "rio",
            "Local classic",
            "$$",
            "4.5",
            "https://maps.google.com/?q=Jobi+Leblon+Rio",
            "🍻",
        ],
        [
            trip_uuid,
            "Pedra do Sal",
            "Historic open-air samba area near the port region. Best for travelers who want a cultural nightlife stop with music and street energy.",
            "Rua Tia Ciata - Saude, Rio de Janeiro - RJ",
            "",
            "5",
            "bars",
            "Centro / Saude",
            "rio",
            "Samba landmark",
            "$",
            "4.8",
            "https://maps.google.com/?q=Pedra+do+Sal+Rio",
            "🥁",
        ],
        [
            trip_uuid,
            "Confeitaria Colombo",
            "Historic 1894 cafe with Belle Epoque architecture, pastries and afternoon tea. A good daytime stop when the group is near Centro.",
            "Rua Goncalves Dias, 32 - Centro, Rio de Janeiro - RJ",
            "",
            "6",
            "cafes",
            "Centro",
            "rio",
            "Historic cafe",
            "$$",
            "4.7",
            "https://maps.google.com/?q=Confeitaria+Colombo+Centro+Rio",
            "☕",
        ],
        [
            trip_uuid,
            "Zona Sul Supermarket",
            "Premium supermarket chain for water, snacks, sunscreen and small essentials at better prices than hotel mini-bars.",
            "Ipanema, Rio de Janeiro - RJ",
            "",
            "7",
            "cafes",
            "Ipanema",
            "rio",
            "Money-saving tip",
            "$",
            "",
            "https://maps.google.com/?q=Zona+Sul+Supermarket+Ipanema+Rio",
            "🛒",
        ],
        [
            trip_uuid,
            "Shopping Leblon",
            "Upscale shopping mall with Brazilian and international brands, restaurants and reliable indoor backup for rainy or very hot periods.",
            "Av. Afranio de Melo Franco, 290 - Leblon, Rio de Janeiro - RJ",
            "",
            "8",
            "shopping",
            "Leblon",
            "rio",
            "Rainy-day backup",
            "$$$",
            "4.6",
            "https://maps.google.com/?q=Shopping+Leblon+Rio",
            "🛍️",
        ],
        [
            trip_uuid,
            "Ipanema Beach",
            "Iconic beach close to the hotel area. Travelers can rent chairs and umbrellas, try mate gelado and walk toward Arpoador for sunset.",
            "Ipanema Beach, Rio de Janeiro - RJ",
            "",
            "9",
            "beaches",
            "Ipanema",
            "rio",
            "Steps from hotel",
            "",
            "4.8",
            "https://maps.google.com/?q=Ipanema+Beach+Rio",
            "🏖️",
        ],
        [
            trip_uuid,
            "Sugarloaf Mountain",
            "Rio landmark reached by cable car from Praia Vermelha and Urca. Best around late afternoon when visibility is good.",
            "Avenida Pasteur, 520 - Urca, Rio de Janeiro - RJ",
            "",
            "10",
            "wellness",
            "Urca",
            "rio",
            "Sunset views",
            "$$$",
            "4.8",
            "https://maps.google.com/?q=Sugarloaf+Mountain+Rio",
            "🌅",
        ],
        [
            trip_uuid,
            "Christ the Redeemer",
            "Major Rio landmark on Corcovado Mountain. Useful context for Day 2 timing, photos and weather-dependent planning.",
            "Corcovado Mountain, Tijuca National Park, Rio de Janeiro - RJ",
            "",
            "11",
            "wellness",
            "Corcovado",
            "rio",
            "Rio icon",
            "$$",
            "4.8",
            "https://maps.google.com/?q=Christ+the+Redeemer+Rio",
            "✨",
        ],
        [
            trip_uuid,
            "Escadaria Selaron",
            "Colorful mosaic staircase between Lapa and Santa Teresa. Good for a short cultural/photo stop with clear safety instructions.",
            "Rua Manuel Carneiro, Santa Teresa, Rio de Janeiro - RJ",
            "",
            "12",
            "shopping",
            "Lapa / Santa Teresa",
            "rio",
            "Photo stop",
            "$",
            "4.6",
            "https://maps.google.com/?q=Escadaria+Selaron+Rio",
            "🎨",
        ],
    ]


def read_recommendations_tab(sheets_svc) -> list[list[str]]:
    response = (
        sheets_svc.spreadsheets()
        .values()
        .get(spreadsheetId=TRIP_CONTENT_SHEET_ID, range="Recomendacoes")
        .execute()
    )
    return response.get("values", [])


def replace_sheet_rows(sheets_svc, trip_uuid: str) -> list[list[str]]:
    rows = read_recommendations_tab(sheets_svc)
    existing = rows[1:] if rows else []
    preserved = [row for row in existing if not row or row[0].strip() != trip_uuid]
    updated = [RECOMMENDATIONS_HEADERS] + preserved + curated_recommendations(trip_uuid)
    sheets_svc.spreadsheets().values().clear(
        spreadsheetId=TRIP_CONTENT_SHEET_ID,
        range="Recomendacoes!A:N",
        body={},
    ).execute()
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=TRIP_CONTENT_SHEET_ID,
        range="Recomendacoes!A1",
        valueInputOption="RAW",
        body={"values": updated},
    ).execute()
    return updated


async def import_to_database(trip_uuid: str, rows: list[list[str]]) -> int:
    recs = parse_recommendations_tab([rows[0]] + [row for row in rows[1:] if row and row[0].strip() == trip_uuid])
    conn = await asyncpg.connect(PG_URL)
    try:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM trip_recommendations WHERE wetravel_trip_uuid = $1",
                trip_uuid,
            )
            for r in recs:
                await conn.execute(
                    """
                    INSERT INTO trip_recommendations
                        (
                            id, wetravel_trip_uuid, name, description, address, photo_url,
                            sort_order, category, neighborhood, location, highlight,
                            price_range, rating, map_url, emoji, created_at, updated_at
                        )
                    VALUES (
                        gen_random_uuid(), $1, $2, $3, $4, $5,
                        $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, now(), now()
                    )
                    """,
                    trip_uuid,
                    r.name,
                    r.description,
                    r.address,
                    r.photo_url,
                    r.sort_order,
                    r.category,
                    r.neighborhood,
                    r.location,
                    r.highlight,
                    r.price_range,
                    r.rating,
                    r.map_url,
                    r.emoji,
                )
    finally:
        await conn.close()
    return len(recs)


async def main(trip_uuid: str) -> None:
    if not TRIP_CONTENT_SHEET_ID:
        raise SystemExit("TRIP_CONTENT_SHEET_ID is not set")
    sheets_svc = build_sheets_client()
    rows = replace_sheet_rows(sheets_svc, trip_uuid)
    imported = await import_to_database(trip_uuid, rows)
    print(f"Populated and imported {imported} recommendations for {trip_uuid}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate rich local recommendations")
    parser.add_argument("--trip-uuid", default="PARROT-RIO-FULL-TEST-2026")
    args = parser.parse_args()
    asyncio.run(main(args.trip_uuid))
