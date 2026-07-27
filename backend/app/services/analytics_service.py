from collections import Counter
from sqlalchemy.orm import Session

from app.schemas.analytics import AnalyticsResponse
from app.services.user_service import get_user_by_github_id
from app.services.repository_service import get_repositories_by_owner
from app.services.health_service import calculate_health_score
from app.services.dormancy_service import calculate_dormancy


def get_developer_analytics(db: Session, github_id: int) -> AnalyticsResponse:
    # 1. Retrieve the user
    user = get_user_by_github_id(db, github_id)
    if user is None:
        raise ValueError("User not found")

    # 2. Retrieve repositories
    repos = get_repositories_by_owner(db, user.id)

    total_repositories = len(repos)
    total_stars = 0
    total_forks = 0
    active_repositories = 0
    dormant_repositories = 0
    total_health_score = 0
    languages = []

    most_popular_repo = None
    max_stars = -1

    most_active_repo = None
    latest_pushed_at = None

    for repo in repos:
        total_stars += repo.stars or 0
        total_forks += repo.forks or 0

        # Dormancy check
        _, dormancy_status, _ = calculate_dormancy(repo)
        if dormancy_status == "Active":
            active_repositories += 1
        elif dormancy_status == "Dormant":
            dormant_repositories += 1

        # Health score check
        health_score, _, _ = calculate_health_score(repo)
        total_health_score += health_score

        # Language tracking
        if repo.language:
            languages.append(repo.language)

        # Most popular repository (highest stars)
        stars_val = repo.stars or 0
        if stars_val > max_stars:
            max_stars = stars_val
            most_popular_repo = repo.name

        # Most active repository (latest pushed_at)
        if repo.pushed_at:
            if latest_pushed_at is None or repo.pushed_at > latest_pushed_at:
                latest_pushed_at = repo.pushed_at
                most_active_repo = repo.name

    average_health_score = 0.0
    if total_repositories > 0:
        average_health_score = float(total_health_score) / total_repositories

    primary_language = None
    if languages:
        counter = Counter(languages)
        primary_language = counter.most_common(1)[0][0]

    return AnalyticsResponse(
        github_id=github_id,
        total_repositories=total_repositories,
        total_stars=total_stars,
        total_forks=total_forks,
        active_repositories=active_repositories,
        dormant_repositories=dormant_repositories,
        average_health_score=round(average_health_score, 2),
        primary_language=primary_language,
        most_popular_repository=most_popular_repo,
        most_active_repository=most_active_repo,
    )
