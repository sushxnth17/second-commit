from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.health import HealthResponse
from app.services.repository_service import get_repository_by_id


def calculate_health_score(repository) -> tuple[int, str, str]:
    # 1. Stars (20)
    stars = repository.stars or 0
    if stars >= 100:
        score_stars = 20
    elif stars >= 50:
        score_stars = 15
    elif stars >= 10:
        score_stars = 10
    elif stars > 0:
        score_stars = 5
    else:
        score_stars = 0

    # 2. Forks (10)
    forks = repository.forks or 0
    if forks >= 50:
        score_forks = 10
    elif forks >= 20:
        score_forks = 8
    elif forks >= 5:
        score_forks = 5
    elif forks > 0:
        score_forks = 2
    else:
        score_forks = 0

    # 3. Open Issues (15)
    open_issues = repository.open_issues
    if open_issues is None or open_issues <= 0:
        score_issues = 15
    elif open_issues <= 10:
        score_issues = 12
    elif open_issues <= 30:
        score_issues = 8
    elif open_issues <= 100:
        score_issues = 4
    else:
        score_issues = 0

    # 4. Recent Activity (30)
    pushed_at = repository.pushed_at
    if pushed_at is None:
        score_activity = 0
    else:
        if pushed_at.tzinfo is None:
            pushed_at = pushed_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - pushed_at
        days = delta.days
        if days <= 30:
            score_activity = 30
        elif days <= 90:
            score_activity = 20
        elif days <= 180:
            score_activity = 15
        elif days <= 365:
            score_activity = 10
        else:
            score_activity = 5

    # 5. Repository Size (5)
    size = repository.size or 0
    if size >= 1000:
        score_size = 5
    elif size > 0:
        score_size = 2
    else:
        score_size = 0

    # 6. Description (5)
    description = repository.description
    if description and description.strip():
        if len(description.strip()) >= 10:
            score_desc = 5
        else:
            score_desc = 3
    else:
        score_desc = 0

    # 7. Default Branch (5)
    default_branch = repository.default_branch
    if default_branch and default_branch.strip() in ["main", "master"]:
        score_branch = 5
    elif default_branch and default_branch.strip():
        score_branch = 3
    else:
        score_branch = 0

    # 8. Language (10)
    language = repository.language
    if language and language.strip():
        score_lang = 10
    else:
        score_lang = 0

    total_score = (
        score_stars +
        score_forks +
        score_issues +
        score_activity +
        score_size +
        score_desc +
        score_branch +
        score_lang
    )

    # Calculate grade and summary
    if total_score >= 90:
        grade = "A"
        summary = "The repository is in excellent health with active development and great community engagement."
    elif total_score >= 80:
        grade = "B"
        summary = "The repository is in good health, showing solid activity and decent engagement."
    elif total_score >= 70:
        grade = "C"
        summary = "The repository has moderate health. Some areas like recent activity or community size could be improved."
    elif total_score >= 60:
        grade = "D"
        summary = "The repository health is low. It might be stale or lacks description/activity."
    else:
        grade = "F"
        summary = "The repository health is critical. It has low activity, few stars, or is missing key metadata."

    return total_score, grade, summary


def get_health(repository_id: int, db: Session) -> HealthResponse:
    # This raises ValueError if not found
    repository = get_repository_by_id(db, repository_id)
    score, grade, summary = calculate_health_score(repository)
    return HealthResponse(
        repository_id=repository.id,
        repository_name=repository.name,
        health_score=score,
        grade=grade,
        summary=summary,
    )
