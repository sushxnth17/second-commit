from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.services.github_service import get_user_repositories

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/repositories/{github_id}")
async def list_repositories(
    github_id: int,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.github_id == github_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not user.access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token not found",
        )

    repos = await get_user_repositories(user.access_token)

    return repos