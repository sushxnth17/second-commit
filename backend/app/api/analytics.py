from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import get_developer_analytics

router = APIRouter(
    prefix="/analytics",
    tags=["Developer Analytics"],
)


@router.get("", response_model=AnalyticsResponse)
async def get_developer_analytics_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_developer_analytics(db, current_user.github_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
