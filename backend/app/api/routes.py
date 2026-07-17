from fastapi import APIRouter

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