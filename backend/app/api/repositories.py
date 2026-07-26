from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.repository import Repository
from app.services.github_service import get_user_repositories, get_repository_details
from app.services.repository_service import (
    get_repository_by_github_id,
    create_repository,
    get_repositories_by_owner,
    update_repository,
)
from app.schemas import RepositoryResponse


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


@router.get("/{github_id}", response_model=list[RepositoryResponse])
async def get_repositories(
    github_id: int,
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

    repositories = get_repositories_by_owner(db, user.id)
    return repositories


@router.post("/{repository_id}/sync", response_model=RepositoryResponse)
async def sync_repository(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    owner = repository.owner
    if not owner or not owner.access_token:
        raise HTTPException(
            status_code=400,
            detail="GitHub access token not found for user",
        )

    try:
        github_data = await get_repository_details(owner.access_token, repository.full_name)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API failure: {e.response.status_code} - {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API connection failure: {str(e)}",
        )

    updated_repository = update_repository(
        db=db,
        db_repo=repository,
        repo_data=github_data,
    )

    return updated_repository