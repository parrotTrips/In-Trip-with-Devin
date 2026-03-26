# Parrot Trips - In-Trip Experience App

Interactive travel companion app for Parrot Trips group experiences in Brazil. Features a game-board style trip progress map, WhatsApp-based authentication, persistent checklists, and collaborative comments.

## Live Demo

- **Frontend:** https://parrottrips-app-ke2ylzmt.devinapps.com
- **Backend API:** https://app-rxxkezkz.fly.dev
- **API Docs:** https://app-rxxkezkz.fly.dev/docs

## Architecture

```
frontend/          React + Vite + TypeScript + Tailwind CSS
backend/           FastAPI + SQLite + WhatsApp Business API
```

### Frontend (React + Vite + TypeScript)

- **Login Screen** - Phone number input with country code selector + 6-digit OTP verification
- **Home Screen (Travel Phase Map)** - Game-board style winding path with pre-trip phases and daily itinerary nodes. Parrot mascot shows ideal pace, traveler avatars show group progress
- **Phase Details** - Checklist items with persistent state, detailed instructions, comments section
- **Day Details** - Chronological activity timeline with types (included/optional/suggested/logistics), descriptions, practical info, images
- **Secret Missions** - Gamification with points and challenges
- **Documents** - Travel documents organized by category

### Backend (FastAPI + SQLite)

- **Auth** - OTP generation + verification via Meta WhatsApp Business API
- **Users** - Registration and profile management
- **Checklist** - Per-user checklist item state persistence
- **Phase Completion** - Track which phases each traveler has completed
- **Comments** - Public comments per phase/day with user attribution

### WhatsApp OTP Flow

1. User enters phone number on login screen
2. Frontend calls `POST /auth/request-otp` with phone number
3. Backend generates 6-digit code, stores in DB, sends via Meta WhatsApp Business API
4. User receives WhatsApp message with code (template: `intripauth`)
5. User enters code, frontend calls `POST /auth/verify-otp`
6. Backend validates code, returns user info + session

## Setup

### Prerequisites

- Node.js 18+
- Python 3.12+
- Poetry (Python package manager)
- Meta WhatsApp Business API credentials

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # Edit with your backend URL
npm run dev             # Development server at http://localhost:5173
npm run build           # Production build to dist/
```

### Backend

```bash
cd backend
poetry install
cp .env.example .env   # Edit with your WhatsApp API credentials
poetry run fastapi dev app/main.py   # Development server at http://localhost:8000
```

### Environment Variables

#### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Backend API URL | `https://app-rxxkezkz.fly.dev` |

#### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | Meta WhatsApp Phone Number ID |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta WhatsApp Business Account ID |
| `WHATSAPP_ACCESS_TOKEN` | Meta WhatsApp API Access Token |
| `WHATSAPP_TEMPLATE_NAME` | WhatsApp message template name (default: `intripauth`) |
| `DATABASE_PATH` | SQLite database path (default: `/data/app.db`) |

### Meta WhatsApp Business API Setup

1. Create an app at [developers.facebook.com](https://developers.facebook.com) (type: "Connect with customers through WhatsApp")
2. In **WhatsApp > API Setup**, note the Phone Number ID and WABA ID
3. Generate a permanent access token via **Business Settings > System Users**
4. Create an authentication template in **WhatsApp > Message Templates** (category: Authentication)
5. Add recipient phone numbers to the allowed list (required while app is in test mode)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/healthz` | Health check |
| `POST` | `/auth/request-otp` | Send OTP via WhatsApp |
| `POST` | `/auth/verify-otp` | Verify OTP and login |
| `GET` | `/users/{user_id}` | Get user info |
| `PUT` | `/users/{user_id}` | Update user profile |
| `POST` | `/checklist/update` | Update checklist item |
| `GET` | `/checklist/{trip_id}/{user_id}` | Get checklist progress |
| `POST` | `/phases/complete` | Mark phase complete |
| `GET` | `/phases/{trip_id}/{user_id}` | Get phase completions |
| `POST` | `/comments` | Add comment |
| `GET` | `/comments/{trip_id}/{phase_id}` | Get comments |

## Current Trip: Bernardo Brazil Trip (Ross26)

- **Dates:** Feb 27 - Mar 8, 2026
- **Locations:** Rio de Janeiro + Ilha Grande
- **Hotels:** Astoria Ipanema (Rio) | Recreio Da Praia (Ilha Grande)
- **Content Source:** `Ross26 In Trip Page Content - - Sheet1.csv`

## Tech Stack

- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, React Router, Lucide Icons
- **Backend:** FastAPI, SQLite (aiosqlite), httpx, Pydantic
- **Auth:** Meta WhatsApp Business API (authentication templates)
- **Deploy:** Frontend on Devin Apps CDN, Backend on Fly.io with persistent volume

## Deployment

### Frontend

```bash
cd frontend
npm run build
# Deploy the dist/ directory to your hosting provider
```

### Backend (Fly.io)

The backend is deployed to Fly.io with a persistent 1GB volume mounted at `/data` for SQLite storage. The WhatsApp API credentials are configured as environment variables.

---

Built with Devin AI for [Parrot Trips](https://www.parrottrips.com)
