from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import dispose_engine
from app.routers.auth import router as auth_router
from app.routers.checklist import router as checklist_router
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """App lifespan: keep shared resources tidy without bootstrapping schema."""
    yield
    await dispose_engine()


app = FastAPI(lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(checklist_router)
