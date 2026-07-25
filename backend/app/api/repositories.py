from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.services.github_service import get_user_repositories
from app.services.repository_service import (
    get_repository_by_github_id,
    create_repository,
)

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post("/import/{github_id}/{repo_id}")
async def import_repository(
    github_id: int,
    repo_id: int,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.github_id == github_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    repos = await get_user_repositories(user.access_token)

    repo = next(
        (r for r in repos if r["id"] == repo_id),
        None,
    )

    if repo is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    existing = get_repository_by_github_id(
        db,
        repo["id"],
    )

    if existing:
        return {
            "message": "Repository already imported",
            "repository": {
                "id": existing.id,
                "name": existing.name,
            },
        }

    repository = create_repository(
        db=db,
        owner_id=user.id,
        repo=repo,
    )

    return {
        "message": "Repository imported successfully",
        "repository": {
            "id": repository.id,
            "name": repository.name,
            "full_name": repository.full_name,
        },
    }