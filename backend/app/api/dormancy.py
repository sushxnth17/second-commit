from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.schemas.dormancy import DormancyResponse
from app.services.dormancy_service import get_repository_dormancy

router = APIRouter(
    prefix="/repositories",
    tags=["Repository Dormancy"],
)


@router.get("/{repository_id}/dormancy", response_model=DormancyResponse)
async def get_repository_dormancy_endpoint(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository or repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    try:
        return get_repository_dormancy(db, repository_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
