from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.schemas.health import HealthResponse
from app.services.health_service import get_health

router = APIRouter(
    prefix="/repositories",
    tags=["Repository Health"],
)


@router.get("/{repository_id}/health", response_model=HealthResponse)
async def get_repository_health(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository or (repository.owner_id != current_user.id and not repository.published):
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    try:
        return get_health(repository_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
