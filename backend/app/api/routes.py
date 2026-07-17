from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "Welcome to SecondCommit API 🚀"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy"
    }


