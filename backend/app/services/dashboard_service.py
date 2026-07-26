from sqlalchemy.orm import Session

from app.schemas.dashboard import DashboardResponse
from app.services.repository_service import get_repositories_by_owner
from app.services.user_service import get_user_by_github_id


def get_dashboard(db: Session, github_id: int) -> DashboardResponse:
    user = get_user_by_github_id(db, github_id)

    if user is None:
        raise ValueError("User not found")

    repositories = get_repositories_by_owner(db, user.id)

    return DashboardResponse(
        user=user,
        repositories=repositories,
        total_repositories=len(repositories),
    )