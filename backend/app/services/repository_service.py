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
    repository = Repository(
        github_repo_id=repo["id"],
        name=repo["name"],
        full_name=repo["full_name"],
        description=repo.get("description"),
        html_url=repo["html_url"],
        language=repo.get("language"),
        default_branch=repo["default_branch"],
        owner_id=owner_id,
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    return repository