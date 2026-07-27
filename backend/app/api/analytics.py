from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import get_developer_analytics

router = APIRouter(
    prefix="/analytics",
    tags=["Developer Analytics"],
)


@router.get("/{github_id}", response_model=AnalyticsResponse)
async def get_developer_analytics_endpoint(
    github_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_developer_analytics(db, github_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
