from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.ai import AIInsightsResponse
from app.services.ai_service import get_ai_insights

router = APIRouter(
    prefix="/repositories",
    tags=["AI Insights"],
)


@router.get("/{repository_id}/ai-insights", response_model=AIInsightsResponse)
async def get_repository_ai_insights_endpoint(
    repository_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_ai_insights(db, repository_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
