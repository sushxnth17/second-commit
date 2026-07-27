from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
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
):
    try:
        return get_repository_dormancy(db, repository_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
