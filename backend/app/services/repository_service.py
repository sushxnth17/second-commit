from datetime import datetime
from sqlalchemy.orm import Session

from app.models.repository import Repository


def get_repository_by_github_id(
    db: Session,
    github_repo_id: int,
):
    return (
        db.query(Repository)
        .filter(Repository.github_repo_id == github_repo_id)
        .first()
    )


def create_repository(
    db: Session,
    owner_id: int,
    repo: dict,
):
    created_at = None
    if repo.get("created_at"):
        created_at = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))

    updated_at = None
    if repo.get("updated_at"):
        updated_at = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))

    pushed_at = None
    if repo.get("pushed_at"):
        pushed_at = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))

    repository = Repository(
        github_repo_id=repo["id"],
        name=repo["name"],
        full_name=repo["full_name"],
        description=repo.get("description"),
        html_url=repo["html_url"],
        language=repo.get("language"),
        default_branch=repo["default_branch"],
        owner_id=owner_id,
        stars=repo.get("stargazers_count"),
        forks=repo.get("forks_count"),
        watchers=repo.get("watchers_count") if repo.get("watchers_count") is not None else repo.get("watchers"),
        open_issues=repo.get("open_issues_count") if repo.get("open_issues_count") is not None else repo.get("open_issues"),
        size=repo.get("size"),
        created_at=created_at,
        updated_at=updated_at,
        pushed_at=pushed_at,
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    return repository


def update_repository(
    db: Session,
    db_repo: Repository,
    repo_data: dict,
) -> Repository:
    db_repo.name = repo_data["name"]
    db_repo.full_name = repo_data["full_name"]
    db_repo.description = repo_data.get("description")
    db_repo.html_url = repo_data["html_url"]
    db_repo.language = repo_data.get("language")
    db_repo.default_branch = repo_data["default_branch"]

    db_repo.stars = repo_data.get("stargazers_count")
    db_repo.forks = repo_data.get("forks_count")
    db_repo.watchers = repo_data.get("watchers_count") if repo_data.get("watchers_count") is not None else repo_data.get("watchers")
    db_repo.open_issues = repo_data.get("open_issues_count") if repo_data.get("open_issues_count") is not None else repo_data.get("open_issues")
    db_repo.size = repo_data.get("size")

    if repo_data.get("created_at"):
        db_repo.created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
    if repo_data.get("updated_at"):
        db_repo.updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
    if repo_data.get("pushed_at"):
        db_repo.pushed_at = datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00"))

    db.commit()
    db.refresh(db_repo)
    return db_repo


def get_repositories_by_owner(db: Session, owner_id: int):
    return (
        db.query(Repository)
        .filter(Repository.owner_id == owner_id)
        .all()
    )


def get_repository_by_id(db: Session, repository_id: int) -> Repository:
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )
    if not repository:
        raise ValueError("Repository not found")
    return repository
