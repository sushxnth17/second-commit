from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.api.github import router as github_router
from app.api.routes import router as root_router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.api.repositories import router as repository_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.dormancy import router as dormancy_router
from app.api.analytics import router as analytics_router

app = FastAPI(
    title="SecondCommit API",
    description="Backend API for the SecondCommit platform.",
    version="0.1.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
)

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(repository_router)
app.include_router(dashboard_router)
app.include_router(health_router)
app.include_router(dormancy_router)
app.include_router(analytics_router)


