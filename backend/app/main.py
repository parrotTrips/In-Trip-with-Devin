from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_app_env, get_cors_allowed_origins
from app.db.session import dispose_engine
from app.middleware.auth import JWTAuthMiddleware
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.checklist import router as checklist_router
from app.routers.console import router as console_router
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.staff import router as staff_router
from app.routers.trip import router as trip_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    yield
    await dispose_engine()


is_development = get_app_env() == "development"
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if is_development else None,
    redoc_url="/redoc" if is_development else None,
    openapi_url="/openapi.json" if is_development else None,
)

# Starlette wraps middleware in reverse registration order. Register the JWT
# middleware first so CORS remains outermost and decorates authentication errors.
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(trip_router)
app.include_router(staff_router)
app.include_router(checklist_router)
app.include_router(console_router)
