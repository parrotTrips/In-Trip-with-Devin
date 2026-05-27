"""
Seed script: popula trip_phases, checklist_items, links e activities com dados placeholder.

Uso:
  python backend/scripts/seed_placeholder_trip.py \
      --trip-uuid <wetravel_trip_uuid> \
      --start-date 2026-02-27

O script é idempotente: apaga os dados existentes para o trip_uuid antes de inserir.
Para criar usuários de teste, use: python backend/scripts/gen_dev_users.py
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Permite rodar de qualquer diretório
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/parrot_trips")
# asyncpg usa "postgresql://", não "postgresql+asyncpg://"
PG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

# ---------------------------------------------------------------------------
# Dados das fases (traduzidos do tripData.ts)
# ---------------------------------------------------------------------------

PRE_TRIP_PHASES = [
    {
        "slug": "visa",
        "phase_type": "pre-trip",
        "title": "Visa",
        "subtitle": "Entry Requirements",
        "icon": "passport",
        "short_description": "Visa requirements for Brazil",
        "detailed_description": (
            "Brazil requires a valid visa or electronic travel authorization for entry depending on your nationality. "
            "US citizens need an eVisa which can be obtained online. Make sure your passport is valid for at least "
            "6 months beyond your travel dates.\n\nProcessing times vary — apply early to avoid last-minute issues. "
            "Keep a printed copy of your visa approval as backup."
        ),
        "sort_order": 0,
        "checklist": [
            "Check if your nationality requires a visa for Brazil",
            "Ensure passport is valid for 6+ months beyond travel dates",
            "Apply for eVisa on the official Brazilian government portal",
            "Save/print visa approval confirmation",
            "Share visa approval with Parrot Trips team",
        ],
        "links": [
            ("Brazil eVisa Portal", "https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos/informacoes-sobre-vistos-para-estrangeiros-viajarem-ao-brasil"),
            ("US Citizens Visa Info", "https://www.gov.br/mre/en/subjects/consular-portal/visas"),
        ],
    },
    {
        "slug": "vaccination",
        "phase_type": "pre-trip",
        "title": "Vaccination",
        "subtitle": "Health Requirements",
        "icon": "syringe",
        "short_description": "Required vaccinations for travel to Brazil",
        "detailed_description": (
            "Yellow Fever vaccination is strongly recommended for travelers visiting Brazil, especially if you plan "
            "to visit areas outside major cities. Some countries require proof of Yellow Fever vaccination for "
            "re-entry after visiting Brazil.\n\nCOVID-19 vaccination is no longer required for entry but is "
            "recommended. Consult your doctor about other recommended vaccines such as Hepatitis A/B, Typhoid, "
            "and routine immunizations.\n\nBring your vaccination card or International Certificate of Vaccination "
            "(yellow card) with you."
        ),
        "sort_order": 1,
        "checklist": [
            "Check CDC/WHO recommendations for Brazil travel vaccines",
            "Get Yellow Fever vaccination (recommended)",
            "Ensure routine vaccinations are up to date",
            "Obtain International Certificate of Vaccination (yellow card)",
            "Pack vaccination card in carry-on luggage",
        ],
        "links": [
            ("CDC Brazil Travel Health", "https://wwwnc.cdc.gov/travel/destinations/traveler/none/brazil"),
            ("WHO Vaccination Requirements", "https://www.who.int/health-topics/vaccines-and-immunization"),
        ],
    },
    {
        "slug": "packing",
        "phase_type": "pre-trip",
        "title": "How to Pack",
        "subtitle": "What to Bring",
        "icon": "luggage",
        "short_description": "Packing essentials for your Brazil trip",
        "detailed_description": (
            "Pack light and smart for Rio de Janeiro and Ilha Grande! The weather will be warm and humid (summer "
            "in Brazil). You'll need beachwear, comfortable walking shoes, and some casual evening outfits.\n\n"
            "Don't forget essentials like sunscreen (SPF 50+), insect repellent, and a reusable water bottle. "
            "For Ilha Grande, pack a small daypack for hikes and quick-dry clothing.\n\n"
            "Remember: Brazilian outlets use Type N plugs (similar to Type C/Europlug). Bring an adapter if needed."
        ),
        "sort_order": 2,
        "checklist": [
            "Light, breathable clothing (shorts, t-shirts, sundresses)",
            "Swimwear and beach towel (or use hotel beach kit)",
            "Comfortable walking shoes + flip flops/sandals",
            "Sunscreen SPF 50+, sunglasses, and hat",
            "Insect repellent (especially for Ilha Grande)",
            "Rain jacket or light poncho (tropical showers)",
            "Power adapter for Brazil (Type N plug)",
            "Reusable water bottle",
            "Small daypack for excursions",
            "Casual evening outfit for dinners",
            "Medications and personal toiletries",
            "Copy of passport and travel insurance in carry-on",
        ],
        "links": [
            ("Brazil Plug Type Guide", "https://www.power-plugs-sockets.com/brazil/"),
            ("Rio de Janeiro Weather Forecast", "https://www.weather.com/weather/tenday/l/Rio+de+Janeiro+Brazil"),
        ],
    },
    {
        "slug": "documents",
        "phase_type": "pre-trip",
        "title": "Documents",
        "subtitle": "Travel Papers",
        "icon": "file-text",
        "short_description": "All travel documents you need for the trip",
        "detailed_description": (
            "Make sure you have all essential travel documents organized and easily accessible. Keep digital copies "
            "of everything in your phone and email, plus printed backups in your carry-on.\n\n"
            "Parrot Trips will provide your hotel confirmations and activity vouchers. You are responsible for your "
            "passport, visa, vaccination records, travel insurance, and flight tickets.\n\n"
            "We recommend keeping a folder with printed copies of all important documents separate from your originals."
        ),
        "sort_order": 3,
        "checklist": [
            "Valid passport (6+ months validity)",
            "Visa/eVisa approval printed",
            "Flight tickets/boarding passes",
            "Travel insurance document",
            "Vaccination card / Yellow Fever certificate",
            "Hotel reservation confirmations",
            "Emergency contact card",
            "Digital copies of all documents saved in phone/email",
            "Pre-Departure Form submitted to Parrot Trips",
        ],
        "links": [
            ("Download Pre-Departure Form", "#"),
            ("Travel Insurance Guide", "#"),
        ],
    },
]

IN_TRIP_DAYS = [
    {
        "slug": "day1",
        "title": "Day 1 — Feb 27",
        "subtitle": "Arrival in Rio",
        "icon": "plane-landing",
        "short_description": "Airport pickup, Hotel Check-in, Ipanema Beach & Welcome Happy Hour",
        "detailed_description": "Welcome to Rio de Janeiro! Get picked up from the airport, check into the Astoria Ipanema Hotel, explore Ipanema Beach, then join us for a Welcome Happy Hour at La Carioca En La Playa.",
        "sort_order": 4,
        "day_offset": 0,
        "activities": [
            {"name": "Airport Pickup", "type": "logistics", "time": "10:00 AM", "duration_minutes": None,
             "description": "We will pick you up on your arrival day according to the details provided in your Pre-Departure Form.", "sort_order": 0},
            {"name": "Hotel Check-in (Astoria Ipanema)", "type": "logistics", "time": "2:00 PM", "duration_minutes": None,
             "description": "Check into the Astoria Ipanema Hotel. Standard check-in from 2PM. Luggage storage available for early arrivals.", "sort_order": 1},
            {"name": "Enjoy Ipanema Beach", "type": "suggested", "time": "3:00 PM", "duration_minutes": 120,
             "description": "Our recommendation is to enjoy Ipanema Beach, just two blocks from the hotel. Optional walk to Copacabana Fort.", "sort_order": 2},
            {"name": "Welcome Happy Hour @ La Carioca En La Playa", "type": "included", "time": "5:00 PM", "duration_minutes": 240,
             "description": "Kick-off at the beach bar La Carioca En La Playa. Open bar included! (Caipirinha, beer, water, soft drinks). Brazilian finger foods. Meet the Parrot staff!", "sort_order": 3},
            {"name": "Our Rio Recommendations", "type": "suggested", "time": "Anytime", "duration_minutes": None,
             "description": "Our curated selection of restaurants, bars, spas, and activities for your free time in Rio!", "sort_order": 4},
        ],
    },
    {
        "slug": "day2",
        "title": "Day 2 — Feb 28",
        "subtitle": "BBQ & Rio Nightlife",
        "icon": "flame",
        "short_description": "Brazilian Barbecue at Bernardo's & explore Rio nightlife",
        "detailed_description": "Experience an authentic Brazilian barbecue (churrasco) hosted by Bernardo, then explore Rio's legendary nightlife scene.",
        "sort_order": 5,
        "day_offset": 1,
        "activities": [
            {"name": "Barbecue @ Bernardo's", "type": "included", "time": "1:00 PM", "duration_minutes": 180,
             "description": "More details coming soon! Transfer from hotel included. Casual dress code. Vegetarian options available.", "sort_order": 0},
            {"name": "Explore Local Bars & Parties", "type": "suggested", "time": "9:00 PM", "duration_minutes": None,
             "description": "Explore Rio's vibrant nightlife! From the iconic bars of Lapa to the trendy spots of Leblon.", "sort_order": 1},
        ],
    },
    {
        "slug": "day3",
        "title": "Day 3 — Mar 1",
        "subtitle": "Christ & Sugarloaf",
        "icon": "mountain",
        "short_description": "Bike Tour, Christ the Redeemer & Sugarloaf Mountain + Samba @ Bosque Bar",
        "detailed_description": "Optional morning bike tour, then visit two of Rio's most iconic landmarks — Christ the Redeemer and Sugarloaf Mountain. In the evening, catch a samba party at Bosque Bar.",
        "sort_order": 6,
        "day_offset": 2,
        "activities": [
            {"name": "Bike Tour", "type": "optional", "time": "9:00 AM", "duration_minutes": 180,
             "description": "Tour time is 3 hours. In total we bike around 2 hours. Includes: Bike – Helmet – Guide. Bring water!", "sort_order": 0},
            {"name": "Christ the Redeemer & Sugarloaf", "type": "included", "time": "7:30 AM", "duration_minutes": 330,
             "description": "07:30 AM departure from hotel lobby. Visit Christ the Redeemer and Sugarloaf Mountain. Return ~01:00 PM.", "sort_order": 1},
            {"name": "Samba Party @ Bosque Bar", "type": "suggested", "time": "8:00 PM", "duration_minutes": None,
             "description": "Rio's official Sunday party! Sambinha do Bosque — live samba/pagode acts and DJs. TT Burger inside for food.", "sort_order": 2},
        ],
    },
    {
        "slug": "day4",
        "title": "Day 4 — Mar 2",
        "subtitle": "Historic Center & Samba",
        "icon": "landmark",
        "short_description": "SUP at Sunrise, Historic Center Tour, Footvolley & Pedra do Sal",
        "detailed_description": "Optional sunrise paddleboarding, then explore Rio's historic center with an expert guide. Afternoon footvolley class and evening samba at Pedra do Sal.",
        "sort_order": 7,
        "day_offset": 3,
        "activities": [
            {"name": "Stand Up Paddle at Sunrise (Copacabana)", "type": "optional", "time": "4:30 AM", "duration_minutes": 120,
             "description": "Departure 4:00 AM from hotel. Paddling from 4:40 to 5:40 AM (Sunrise at 5:10 AM). Return ~6:30 AM. Difficulty: Easy to moderate.", "sort_order": 0},
            {"name": "Historic Center Tour", "type": "included", "time": "9:00 AM", "duration_minutes": 240,
             "description": "09:00 AM departure. Explore Rio's historic landmarks with an expert local guide. Walk through colonial streets, visit churches, Royal Portuguese Reading Room. Return ~1:00 PM.", "sort_order": 1},
            {"name": "Footvolley Class", "type": "optional", "time": "3:00 PM", "duration_minutes": 60,
             "description": "1-hour class on Ipanema beach. All levels welcome. Wear light sportswear or swimwear.", "sort_order": 2},
            {"name": "Samba da Pedra do Sal", "type": "included", "time": "6:30 PM", "duration_minutes": 300,
             "description": "The birthplace of samba! Open-air street party with live acoustic samba. Monday is the most famous day. No tickets required — free public event.", "sort_order": 3},
        ],
    },
    {
        "slug": "day5",
        "title": "Day 5 — Mar 3",
        "subtitle": "Beach & Dois Irmãos",
        "icon": "sun",
        "short_description": "Beach time, Dois Irmãos Hike & Favela Vidigal Tour",
        "detailed_description": "Relaxed morning at the beach, then hike to the top of Dois Irmãos for one of the best views in Rio, passing through Vidigal Favela.",
        "sort_order": 8,
        "day_offset": 4,
        "activities": [
            {"name": "Beach Time", "type": "suggested", "time": "9:00 AM", "duration_minutes": 180,
             "description": "Enjoy the morning at Ipanema or Copacabana beach! The hotel is steps from Ipanema beach.", "sort_order": 0},
            {"name": "Dois Irmãos Hike & Favela Vidigal Tour", "type": "included", "time": "1:30 PM", "duration_minutes": 270,
             "description": "Leave hotel at 1:30 PM. Meet local guide at Vidigal. Hike up Dois Irmãos trail with panoramic views of Rio. ~3-4 hours total.", "sort_order": 1},
        ],
    },
    {
        "slug": "day6",
        "title": "Day 6 — Mar 4",
        "subtitle": "Rio → Ilha Grande",
        "icon": "ship",
        "short_description": "Transfer to Ilha Grande Island & Brazilian Dance Class",
        "detailed_description": "Say goodbye to Rio and journey to the paradise island of Ilha Grande! Bus + boat transfer, beachfront hotel, and Forró dance lesson.",
        "sort_order": 9,
        "day_offset": 5,
        "activities": [
            {"name": "Departure to Ilha Grande (Bus + Boat)", "type": "logistics", "time": "8:00 AM", "duration_minutes": 300,
             "description": "Depart from Astoria Hotel at 08:00 AM. ~3 hours driving + 1-hour boat ride to Ilha Grande.", "sort_order": 0},
            {"name": "Hotel Check-in (Recreio Da Praia)", "type": "logistics", "time": "2:00 PM", "duration_minutes": None,
             "description": "Check into Recreio Da Praia hotel on Ilha Grande. Check-in from 2:00 PM. Breakfast 07:00–10:00 AM.", "sort_order": 1},
            {"name": "Forró Dance Lesson & Caipirinha Workshop", "type": "included", "time": "5:00 PM", "duration_minutes": 120,
             "description": "Immerse yourself in authentic Brazilian rhythms! Energetic Forró dance lesson followed by a hands-on Caipirinha mixology workshop.", "sort_order": 2},
        ],
    },
    {
        "slug": "day7",
        "title": "Day 7 — Mar 5",
        "subtitle": "Boat Ride",
        "icon": "sailboat",
        "short_description": "Private boat ride around Ilha Grande with swim stops & lunch",
        "detailed_description": "The highlight of Ilha Grande! Private boat tour with swim stops, snorkeling, lunch onboard, and open bar.",
        "sort_order": 10,
        "day_offset": 6,
        "activities": [
            {"name": "Private Boat Ride", "type": "included", "time": "10:30 AM", "duration_minutes": 390,
             "description": "Exclusive private boat tour for our group. 2–3 scenic swim stops for swimming and snorkeling. Lunch onboard and open bar (caipirinhas + cold beer). Return ~5:00 PM.", "sort_order": 0},
            {"name": "Free Night", "type": "suggested", "time": "7:00 PM", "duration_minutes": None,
             "description": "Free evening on the island! Explore village restaurants, grab drinks at a beach bar, or relax.", "sort_order": 1},
        ],
    },
    {
        "slug": "day8",
        "title": "Day 8 — Mar 6",
        "subtitle": "Beach & Goodbye Dinner",
        "icon": "palmtree",
        "short_description": "Free beach day, optional canoeing/hike & farewell dinner",
        "detailed_description": "A relaxed day to enjoy Ilha Grande at your own pace — then the unforgettable Goodbye Dinner at Bonito Paraíso restaurant.",
        "sort_order": 11,
        "day_offset": 7,
        "activities": [
            {"name": "Free Beach Day", "type": "suggested", "time": "9:00 AM", "duration_minutes": None,
             "description": "Enjoy Ilha Grande's stunning beaches at your own pace. Beaches near the village accessible on foot.", "sort_order": 0},
            {"name": "Optional: Canoeing or Hike", "type": "optional", "time": "Flexible", "duration_minutes": 150,
             "description": "For the adventurous! Rent a canoe to explore the coastline or take one of the island's hiking trails.", "sort_order": 1},
            {"name": "Goodbye Dinner", "type": "included", "time": "7:30 PM", "duration_minutes": 180,
             "description": "The Grand Finale! Farewell dinner at Bonito Paraíso restaurant. 07:30 PM departure from pier. Smart casual dress code.", "sort_order": 2},
        ],
    },
    {
        "slug": "day9",
        "title": "Day 9 — Mar 7",
        "subtitle": "Return to Rio",
        "icon": "bus",
        "short_description": "Return to Rio de Janeiro via boat + bus",
        "detailed_description": "Journey back from Ilha Grande to Rio with a boat ride, bus transfer, and airport drop-offs.",
        "sort_order": 12,
        "day_offset": 8,
        "activities": [
            {"name": "Return to Rio de Janeiro (Boat + Bus)", "type": "logistics", "time": "10:00 AM", "duration_minutes": 360,
             "description": "Journey back from Ilha Grande to Rio. Scenic boat ride + bus transfer. GIG Airport drop-off available for travelers departing today (~4:00 PM).", "sort_order": 0},
        ],
    },
    {
        "slug": "day10",
        "title": "Day 10 — Mar 8",
        "subtitle": "Departure",
        "icon": "plane",
        "short_description": "Airport transfers — until next time!",
        "detailed_description": "The final day! Airport transfers arranged according to your departure form. Safe travels!",
        "sort_order": 13,
        "day_offset": 9,
        "activities": [
            {"name": "Transfer to Airport", "type": "logistics", "time": "4:00 PM", "duration_minutes": 90,
             "description": "Group transfer from Astoria Ipanema to GIG International Airport.", "sort_order": 0},
        ],
    },
]


async def seed(trip_uuid: str, start_date: datetime) -> None:
    conn = await asyncpg.connect(PG_URL)
    try:
        async with conn.transaction():
            print(f"Conectando ao banco... OK")
            print(f"Apagando dados existentes para trip_uuid={trip_uuid!r}...")

            # Apagar na ordem inversa das FKs
            phase_ids = await conn.fetch(
                "SELECT id FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
            )
            if phase_ids:
                ids = [str(r["id"]) for r in phase_ids]
                # traveler progress deve vir primeiro (FK → checklist_items e phases)
                traveler_ids = await conn.fetch(
                    "SELECT id FROM trip_travelers WHERE wetravel_trip_uuid = $1", trip_uuid
                )
                if traveler_ids:
                    tt_ids = [str(r["id"]) for r in traveler_ids]
                    await conn.execute(
                        "DELETE FROM traveler_checklist_progress WHERE trip_traveler_id = ANY($1::uuid[])", tt_ids
                    )
                    await conn.execute(
                        "DELETE FROM traveler_phase_progress WHERE trip_traveler_id = ANY($1::uuid[])", tt_ids
                    )
                await conn.execute(
                    "DELETE FROM trip_activities WHERE trip_phase_id = ANY($1::uuid[])", ids
                )
                await conn.execute(
                    "DELETE FROM trip_phase_checklist_items WHERE trip_phase_id = ANY($1::uuid[])", ids
                )
                await conn.execute(
                    "DELETE FROM trip_phase_links WHERE trip_phase_id = ANY($1::uuid[])", ids
                )
                await conn.execute(
                    "DELETE FROM trip_phases WHERE wetravel_trip_uuid = $1", trip_uuid
                )

            print("Inserindo fases pre-trip...")
            phase_id_map: dict[str, str] = {}
            for phase in PRE_TRIP_PHASES:
                phase_id = str(uuid.uuid4())
                phase_id_map[phase["slug"]] = phase_id
                await conn.execute(
                    """
                    INSERT INTO trip_phases
                        (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                         short_description, detailed_description, sort_order,
                         is_locked_by_default, is_visible, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,now(),now())
                    """,
                    phase_id, trip_uuid, phase["phase_type"], phase["title"],
                    phase.get("subtitle"), phase["icon"], phase["short_description"],
                    phase.get("detailed_description"), phase["sort_order"],
                    False, True,
                )
                for i, label in enumerate(phase["checklist"]):
                    await conn.execute(
                        """
                        INSERT INTO trip_phase_checklist_items
                            (id, trip_phase_id, label, sort_order, is_required, created_at, updated_at)
                        VALUES ($1,$2,$3,$4,$5,now(),now())
                        """,
                        str(uuid.uuid4()), phase_id, label, i, True,
                    )
                for i, (label, url) in enumerate(phase["links"]):
                    await conn.execute(
                        """
                        INSERT INTO trip_phase_links
                            (id, trip_phase_id, label, url, sort_order, created_at, updated_at)
                        VALUES ($1,$2,$3,$4,$5,now(),now())
                        """,
                        str(uuid.uuid4()), phase_id, label, url, i,
                    )

            print("Inserindo dias de viagem e atividades...")
            for day in IN_TRIP_DAYS:
                phase_id = str(uuid.uuid4())
                phase_id_map[day["slug"]] = phase_id
                day_starts_at = start_date + timedelta(days=day["day_offset"])
                await conn.execute(
                    """
                    INSERT INTO trip_phases
                        (id, wetravel_trip_uuid, phase_type, title, subtitle, icon,
                         short_description, detailed_description, sort_order,
                         starts_at, is_locked_by_default, is_visible, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,now(),now())
                    """,
                    phase_id, trip_uuid, "in-trip", day["title"],
                    day.get("subtitle"), day["icon"], day["short_description"],
                    day.get("detailed_description"), day["sort_order"],
                    day_starts_at, False, True,
                )
                for act in day["activities"]:
                    await conn.execute(
                        """
                        INSERT INTO trip_activities
                            (id, trip_phase_id, name, activity_type,
                             duration_minutes, short_description, practical_info,
                             sort_order, created_at, updated_at)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,now(),now())
                        """,
                        str(uuid.uuid4()), phase_id, act["name"], act["type"],
                        act.get("duration_minutes"), act["description"],
                        None,  # practical_info — disponível no mock mas omitido por brevidade
                        act["sort_order"],
                    )

        print("\n✅ Seed concluído com sucesso!")
        print(f"   Trip UUID: {trip_uuid}")
        print(f"   Fases inseridas: {len(PRE_TRIP_PHASES) + len(IN_TRIP_DAYS)}")
        total_activities = sum(len(d["activities"]) for d in IN_TRIP_DAYS)
        total_checklist = sum(len(p["checklist"]) for p in PRE_TRIP_PHASES)
        total_links = sum(len(p["links"]) for p in PRE_TRIP_PHASES)
        print(f"   Checklist items: {total_checklist}")
        print(f"   Links: {total_links}")
        print(f"   Atividades: {total_activities}")

    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de dados placeholder para uma viagem")
    parser.add_argument("--trip-uuid", required=True, help="wetravel_trip_uuid da viagem em wetravel_trips")
    parser.add_argument("--start-date", required=True, help="Data de início da viagem (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        print("Erro: --start-date deve estar no formato YYYY-MM-DD")
        sys.exit(1)

    asyncio.run(seed(args.trip_uuid, start_date))


if __name__ == "__main__":
    main()
