from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.github_service import get_user_repositories

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/repositories")
async def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token not found",
        )

    repos = await get_user_repositories(current_user.access_token)

    return repos