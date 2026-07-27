from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.dormancy import DormancyResponse
from app.services.repository_service import get_repository_by_id


def calculate_dormancy(repository) -> tuple[int | None, str, str]:
    pushed_at = repository.pushed_at
    if pushed_at is None:
        return None, "Unknown", "No push activity recorded for this repository."

    if pushed_at.tzinfo is None:
        pushed_at = pushed_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - pushed_at
    days_since_last_push = delta.days

    if days_since_last_push < 0:
        days_since_last_push = 0

    if days_since_last_push <= 30:
        status = "Active"
        message = f"This repository is actively maintained. Last push was {days_since_last_push} days ago."
    elif days_since_last_push <= 90:
        status = "Slowing Down"
        message = f"Activity has slowed down. Last push was {days_since_last_push} days ago."
    elif days_since_last_push <= 180:
        status = "Dormant"
        message = f"This repository is dormant. Last push was {days_since_last_push} days ago."
    else:
        status = "Archived Candidate"
        message = f"This repository is a candidate for archiving. Last push was {days_since_last_push} days ago."

    return days_since_last_push, status, message


def get_repository_dormancy(db: Session, repository_id: int) -> DormancyResponse:
    repository = get_repository_by_id(db, repository_id)
    days, status, message = calculate_dormancy(repository)
    return DormancyResponse(
        repository_id=repository.id,
        repository_name=repository.name,
        days_since_last_push=days,
        status=status,
        message=message,
    )
