from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router as root_router
from app.api.auth import router as auth_router
from app.core.config import settings

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