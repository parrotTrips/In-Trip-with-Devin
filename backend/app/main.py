from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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
