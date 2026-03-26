from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import aiosqlite
import httpx
import os
import random
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# WhatsApp Business API config
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_TEMPLATE_NAME = os.environ.get("WHATSAPP_TEMPLATE_NAME", "intripauth")
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/app.db")


async def init_db():
    """Initialize the SQLite database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
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
        """)
        await db.execute("""
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
        """)
        await db.execute("""
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
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
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
        """)
        await db.execute("""
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
        """)
        await db.execute("""
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
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mission_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mission_id INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (mission_id) REFERENCES missions(id),
                UNIQUE(user_id, mission_id)
            )
        """)
        # Seed default missions if empty
        cursor = await db.execute("SELECT COUNT(*) FROM missions")
        count = (await cursor.fetchone())[0]
        if count == 0:
            default_missions = [
                ('ross26', 'First Photo!', 'Upload your first photo to the group album', 50, '📸', 'social', 1),
                ('ross26', 'Social Butterfly', 'Comment on 3 different activities', 100, '🦋', 'social', 2),
                ('ross26', 'Early Bird', 'Complete all your registration details before the trip', 200, '🐦', 'preparation', 3),
                ('ross26', 'Adventure Seeker', 'Join at least 2 optional activities', 150, '🏄', 'adventure', 4),
                ('ross26', 'Memory Maker', 'Share 10 photos across the trip', 300, '🌟', 'social', 5),
                ('ross26', 'Group Leader', 'Help 3 travelers with their preparation', 250, '👑', 'social', 6),
                ('ross26', 'Beach Explorer', 'Visit 3 different beaches during the trip', 150, '🏖️', 'adventure', 7),
                ('ross26', 'Foodie Tour', 'Try food at 5 different local restaurants', 200, '🍽️', 'adventure', 8),
                ('ross26', 'Culture Vulture', 'Visit Cristo Redentor and Pão de Açúcar', 175, '🏛️', 'adventure', 9),
                ('ross26', 'Night Owl', 'Attend 3 evening events or nightlife activities', 200, '🦉', 'adventure', 10),
                ('ross26', 'Island Life', 'Complete all Ilha Grande activities', 250, '🏝️', 'adventure', 11),
                ('ross26', 'Samba Spirit', 'Dance samba at a local venue', 100, '💃', 'culture', 12),
            ]
            await db.executemany(
                "INSERT INTO missions (trip_id, title, description, points, icon, category, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                default_missions
            )
        await db.commit()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """App lifespan: initialize database on startup."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# ── Pydantic Models ──────────────────────────────────────────────

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    code: str

class ChecklistUpdate(BaseModel):
    trip_id: str
    phase_id: str
    item_id: str
    completed: bool

class PhaseCompletionUpdate(BaseModel):
    trip_id: str
    phase_id: str
    completed: bool

class CommentCreate(BaseModel):
    trip_id: str
    phase_id: str
    text: str
    is_private: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None

class NotificationCreate(BaseModel):
    user_id: int
    trip_id: str = 'ross26'
    title: str
    body: str
    type: str = 'info'  # info, reminder, alert, update
    link: Optional[str] = None

class MissionCreate(BaseModel):
    trip_id: str = 'ross26'
    title: str
    description: str
    points: int = 50
    icon: str = '🎯'
    category: str = 'general'
    sort_order: int = 0

class MissionComplete(BaseModel):
    mission_id: int

class ProfileUpdate(BaseModel):
    preferred_name: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    transfer_platform: Optional[str] = None
    package_option: Optional[str] = None
    num_people: Optional[int] = None
    usd_amount: Optional[float] = None
    proof_of_transfer: Optional[str] = None
    dietary_restrictions_yn: Optional[str] = None
    dietary_restrictions_desc: Optional[str] = None
    seasickness_yn: Optional[str] = None
    first_name_passport: Optional[str] = None
    last_name_passport: Optional[str] = None
    passport_country: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issue_date: Optional[str] = None
    passport_expiration_date: Optional[str] = None
    plus_one_yn: Optional[str] = None
    plus_one_name: Optional[str] = None
    plus_one_email: Optional[str] = None
    intl_flights_help_yn: Optional[str] = None
    intl_flights_help_details: Optional[str] = None
    travel_insurance_help_yn: Optional[str] = None
    unforgettable_trip_details: Optional[str] = None
    receive_addon_updates: Optional[str] = None
    esim_qr_image: Optional[str] = None
    roommate_user_id: Optional[int] = None
    arrival_date: Optional[str] = None
    arrival_time: Optional[str] = None
    arrival_flight: Optional[str] = None
    departure_date: Optional[str] = None
    departure_time: Optional[str] = None
    departure_flight: Optional[str] = None
    service_agreement_url: Optional[str] = None


# ── Health Check ─────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# ── Auth Endpoints ───────────────────────────────────────────────

async def send_whatsapp_otp(phone: str, code: str) -> bool:
    """Send OTP code via Meta WhatsApp Business API."""
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp API not configured, skipping send")
        return False

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone.replace("+", "").replace(" ", "").replace("-", ""),
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": code}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {"type": "text", "text": code}
                    ]
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers=headers,
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info(f"WhatsApp OTP sent successfully to {phone}")
                return True
            else:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp API exception: {e}")
        return False


@app.post("/auth/request-otp")
async def request_otp(req: OTPRequest):
    """Generate OTP and send via WhatsApp Business API."""
    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO otp_codes (phone, code, expires_at) VALUES (?, ?, ?)",
            (req.phone, code, expires_at.isoformat())
        )
        await db.commit()

    # Send OTP via WhatsApp
    whatsapp_sent = await send_whatsapp_otp(req.phone, code)

    response_data = {"message": "OTP sent successfully"}

    # Include debug_code only if WhatsApp sending failed (fallback for testing)
    if not whatsapp_sent:
        response_data["debug_code"] = code
        response_data["message"] = "OTP generated (WhatsApp delivery failed, showing code for testing)"

    return response_data


@app.post("/auth/verify-otp")
async def verify_otp(req: OTPVerify):
    """Verify OTP code and return user info."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM otp_codes
               WHERE phone = ? AND code = ? AND used = FALSE
               ORDER BY created_at DESC LIMIT 1""",
            (req.phone, req.code)
        )
        otp = await cursor.fetchone()

        if not otp:
            raise HTTPException(status_code=400, detail="Invalid OTP code")

        if datetime.fromisoformat(otp["expires_at"]) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP code expired")

        # Mark OTP as used
        await db.execute("UPDATE otp_codes SET used = TRUE WHERE id = ?", (otp["id"],))

        # Create or get user
        cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (req.phone,))
        user = await cursor.fetchone()

        if not user:
            await db.execute("INSERT INTO users (phone) VALUES (?)", (req.phone,))
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (req.phone,))
            user = await cursor.fetchone()
        else:
            await db.commit()

        return {
            "user_id": user["id"],
            "phone": user["phone"],
            "name": user["name"],
            "message": "Login successful"
        }


# ── User Endpoints ───────────────────────────────────────────────

@app.put("/users/{user_id}")
async def update_user(user_id: int, update: UserUpdate):
    """Update user profile."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if update.name is not None:
            await db.execute("UPDATE users SET name = ? WHERE id = ?", (update.name, user_id))
        await db.commit()
    return {"message": "User updated"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user info."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user["id"],
            "phone": user["phone"],
            "name": user["name"],
        }


# ── Profile Endpoints ────────────────────────────────────────────

@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    """Get user profile with all registration and trip details."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        profile = await cursor.fetchone()

        # Also get user basic info
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get roommate info if set
        roommate_info = None
        if profile and profile["roommate_user_id"]:
            cursor = await db.execute("SELECT id, name, phone FROM users WHERE id = ?", (profile["roommate_user_id"],))
            roommate = await cursor.fetchone()
            if roommate:
                roommate_info = {"id": roommate["id"], "name": roommate["name"], "phone": roommate["phone"]}

        if not profile:
            return {
                "user_id": user_id,
                "phone": user["phone"],
                "name": user["name"],
                "profile": None,
                "roommate": roommate_info,
            }

        profile_dict = {key: profile[key] for key in profile.keys() if key not in ("id", "user_id", "trip_id", "updated_at")}
        return {
            "user_id": user_id,
            "phone": user["phone"],
            "name": user["name"],
            "profile": profile_dict,
            "roommate": roommate_info,
        }


@app.put("/profile/{user_id}")
async def update_profile(user_id: int, update: ProfileUpdate):
    """Update user profile. Creates profile if it doesn't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check user exists
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Check if profile exists
        cursor = await db.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        existing = await cursor.fetchone()

        update_data = update.model_dump(exclude_none=True)
        if not update_data:
            return {"message": "No fields to update"}

        if existing:
            set_clauses = ", ".join(f"{k} = ?" for k in update_data)
            values = list(update_data.values()) + [user_id]
            await db.execute(
                f"UPDATE user_profiles SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                values
            )
        else:
            update_data["user_id"] = user_id
            columns = ", ".join(update_data.keys())
            placeholders = ", ".join("?" for _ in update_data)
            await db.execute(
                f"INSERT INTO user_profiles ({columns}) VALUES ({placeholders})",
                list(update_data.values())
            )

        # Also update user name if preferred_name is set
        if update.preferred_name:
            await db.execute("UPDATE users SET name = ? WHERE id = ?", (update.preferred_name, user_id))

        await db.commit()
    return {"message": "Profile updated"}


@app.get("/trip/{trip_id}/travelers")
async def get_trip_travelers(trip_id: str):
    """Get all travelers for a trip (for roommate selection)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, name, phone FROM users ORDER BY id")
        rows = await cursor.fetchall()
        return {
            "trip_id": trip_id,
            "travelers": [
                {"id": row["id"], "name": row["name"], "phone": row["phone"]}
                for row in rows
            ]
        }


# ── Notification Endpoints ───────────────────────────────────────

@app.get("/notifications/{user_id}")
async def get_notifications(user_id: int, unread_only: bool = False):
    """Get notifications for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            query += " AND read = FALSE"
        query += " ORDER BY created_at DESC LIMIT 50"
        cursor = await db.execute(query, (user_id,))
        rows = await cursor.fetchall()
        return {
            "notifications": [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "body": row["body"],
                    "type": row["type"],
                    "link": row["link"],
                    "read": bool(row["read"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
            "unread_count": sum(1 for row in rows if not row["read"]),
        }


@app.get("/notifications/{user_id}/count")
async def get_unread_count(user_id: int):
    """Get unread notification count."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND read = FALSE",
            (user_id,)
        )
        row = await cursor.fetchone()
        return {"unread_count": row[0] if row else 0}


@app.post("/notifications")
async def create_notification(notif: NotificationCreate):
    """Create a notification for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO notifications (user_id, trip_id, title, body, type, link)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (notif.user_id, notif.trip_id, notif.title, notif.body, notif.type, notif.link)
        )
        await db.commit()
    return {"message": "Notification created"}


@app.post("/notifications/broadcast")
async def broadcast_notification(title: str, body: str, trip_id: str = 'ross26', type: str = 'info', link: Optional[str] = None):
    """Send a notification to all users in a trip."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT id FROM users")
        users = await cursor.fetchall()
        for user_row in users:
            await db.execute(
                """INSERT INTO notifications (user_id, trip_id, title, body, type, link)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_row[0], trip_id, title, body, type, link)
            )
        await db.commit()
    return {"message": f"Notification sent to {len(users)} users"}


@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark a notification as read."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE notifications SET read = TRUE WHERE id = ?", (notification_id,))
        await db.commit()
    return {"message": "Notification marked as read"}


@app.put("/notifications/{user_id}/read-all")
async def mark_all_read(user_id: int):
    """Mark all notifications as read for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE notifications SET read = TRUE WHERE user_id = ?", (user_id,))
        await db.commit()
    return {"message": "All notifications marked as read"}


# ── Secret Missions Endpoints ───────────────────────────────────

@app.get("/missions/{trip_id}")
async def get_missions(trip_id: str, user_id: Optional[int] = None):
    """Get all missions for a trip, optionally with user completion status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM missions WHERE trip_id = ? AND active = TRUE ORDER BY sort_order",
            (trip_id,)
        )
        missions = await cursor.fetchall()

        completed_ids: set[int] = set()
        if user_id:
            cursor = await db.execute(
                "SELECT mission_id FROM mission_completions WHERE user_id = ?",
                (user_id,)
            )
            completed_ids = {row["mission_id"] for row in await cursor.fetchall()}

        return {
            "trip_id": trip_id,
            "missions": [
                {
                    "id": m["id"],
                    "title": m["title"],
                    "description": m["description"],
                    "points": m["points"],
                    "icon": m["icon"],
                    "category": m["category"],
                    "completed": m["id"] in completed_ids,
                }
                for m in missions
            ],
        }


@app.post("/missions/{trip_id}/complete")
async def complete_mission(trip_id: str, user_id: int, body: MissionComplete):
    """Mark a mission as completed for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Verify mission exists and belongs to trip
        cursor = await db.execute(
            "SELECT id, points, title FROM missions WHERE id = ? AND trip_id = ?",
            (body.mission_id, trip_id)
        )
        mission = await cursor.fetchone()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        # Check if already completed
        cursor = await db.execute(
            "SELECT id FROM mission_completions WHERE user_id = ? AND mission_id = ?",
            (user_id, body.mission_id)
        )
        if await cursor.fetchone():
            return {"message": "Mission already completed", "already_completed": True}

        await db.execute(
            "INSERT INTO mission_completions (user_id, mission_id) VALUES (?, ?)",
            (user_id, body.mission_id)
        )
        await db.commit()
    return {"message": "Mission completed!", "points_earned": mission[1], "already_completed": False}


@app.delete("/missions/{trip_id}/uncomplete")
async def uncomplete_mission(trip_id: str, user_id: int, body: MissionComplete):
    """Unmark a mission completion for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM mission_completions WHERE user_id = ? AND mission_id = ?",
            (user_id, body.mission_id)
        )
        await db.commit()
    return {"message": "Mission uncompleted"}


@app.get("/missions/{trip_id}/leaderboard")
async def get_leaderboard(trip_id: str):
    """Get points leaderboard for a trip."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT u.id, u.name, u.phone,
                   COALESCE(SUM(m.points), 0) as total_points,
                   COUNT(mc.id) as missions_completed
            FROM users u
            LEFT JOIN mission_completions mc ON u.id = mc.user_id
            LEFT JOIN missions m ON mc.mission_id = m.id AND m.trip_id = ?
            GROUP BY u.id
            ORDER BY total_points DESC
        """, (trip_id,))
        rows = await cursor.fetchall()

        return {
            "trip_id": trip_id,
            "leaderboard": [
                {
                    "user_id": row["id"],
                    "name": row["name"] or row["phone"],
                    "total_points": row["total_points"],
                    "missions_completed": row["missions_completed"],
                }
                for row in rows
            ],
        }


@app.get("/missions/{trip_id}/user/{user_id}/points")
async def get_user_points(trip_id: str, user_id: int):
    """Get total points for a specific user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT COALESCE(SUM(m.points), 0) as total_points,
                   COUNT(mc.id) as missions_completed
            FROM mission_completions mc
            JOIN missions m ON mc.mission_id = m.id
            WHERE mc.user_id = ? AND m.trip_id = ?
        """, (user_id, trip_id))
        row = await cursor.fetchone()
        return {
            "user_id": user_id,
            "total_points": row[0] if row else 0,
            "missions_completed": row[1] if row else 0,
        }


@app.post("/missions")
async def create_mission(mission: MissionCreate):
    """Create a new mission (admin endpoint)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO missions (trip_id, title, description, points, icon, category, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (mission.trip_id, mission.title, mission.description, mission.points, mission.icon, mission.category, mission.sort_order)
        )
        await db.commit()
    return {"message": "Mission created"}


# ── Checklist Endpoints ─────────────────────────────────────────

@app.post("/checklist/update")
async def update_checklist_item(user_id: int, update: ChecklistUpdate):
    """Update a single checklist item's completion status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO checklist_progress (user_id, trip_id, phase_id, item_id, completed, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, trip_id, phase_id, item_id)
            DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
        """, (user_id, update.trip_id, update.phase_id, update.item_id, update.completed, update.completed))
        await db.commit()
    return {"message": "Checklist item updated"}


@app.get("/checklist/{trip_id}/{user_id}")
async def get_checklist_progress(trip_id: str, user_id: int):
    """Get all checklist progress for a user in a trip."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT phase_id, item_id, completed FROM checklist_progress WHERE user_id = ? AND trip_id = ?",
            (user_id, trip_id)
        )
        rows = await cursor.fetchall()

        progress: dict[str, dict[str, bool]] = {}
        for row in rows:
            phase_id = row["phase_id"]
            if phase_id not in progress:
                progress[phase_id] = {}
            progress[phase_id][row["item_id"]] = bool(row["completed"])

        return {"trip_id": trip_id, "user_id": user_id, "progress": progress}


# ── Phase Completion Endpoints ───────────────────────────────────

@app.post("/phases/complete")
async def update_phase_completion(user_id: int, update: PhaseCompletionUpdate):
    """Mark a phase as completed/incomplete for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO phase_completion (user_id, trip_id, phase_id, completed, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, trip_id, phase_id)
            DO UPDATE SET completed = ?, updated_at = CURRENT_TIMESTAMP
        """, (user_id, update.trip_id, update.phase_id, update.completed, update.completed))
        await db.commit()
    return {"message": "Phase completion updated"}


@app.get("/phases/{trip_id}/{user_id}")
async def get_phase_completions(trip_id: str, user_id: int):
    """Get all phase completions for a user in a trip."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT phase_id, completed FROM phase_completion WHERE user_id = ? AND trip_id = ?",
            (user_id, trip_id)
        )
        rows = await cursor.fetchall()
        completions = {row["phase_id"]: bool(row["completed"]) for row in rows}
        return {"trip_id": trip_id, "user_id": user_id, "completions": completions}


# ── Comments Endpoints ───────────────────────────────────────────

@app.post("/comments")
async def add_comment(user_id: int, comment: CommentCreate):
    """Add a comment to a phase."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO comments (user_id, trip_id, phase_id, text, is_private)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, comment.trip_id, comment.phase_id, comment.text, comment.is_private)
        )
        await db.commit()
    return {"message": "Comment added"}


@app.get("/comments/{trip_id}/{phase_id}")
async def get_comments(trip_id: str, phase_id: str):
    """Get all public comments for a phase."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT c.id, c.text, c.created_at, c.is_private,
                      u.id as user_id, u.name as user_name, u.phone as user_phone
               FROM comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.trip_id = ? AND c.phase_id = ? AND c.is_private = FALSE
               ORDER BY c.created_at ASC""",
            (trip_id, phase_id)
        )
        rows = await cursor.fetchall()
        comments_list = [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "user_name": row["user_name"] or row["user_phone"],
                "text": row["text"],
                "created_at": row["created_at"],
                "is_private": bool(row["is_private"]),
            }
            for row in rows
        ]
        return {"trip_id": trip_id, "phase_id": phase_id, "comments": comments_list}
