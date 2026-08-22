from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.services.github_service import get_user_repositories, get_repository_details
from app.services.repository_service import (
    get_repository_by_github_id,
    create_repository,
    get_repositories_by_owner,
    update_repository,
    get_repository_by_id,
)
from app.schemas import RepositoryResponse


router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post("/import/{repo_id}")
async def import_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token not found",
        )

    repos = await get_user_repositories(current_user.access_token)

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
        owner_id=current_user.id,
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


@router.get("", response_model=list[RepositoryResponse])
async def list_user_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_repositories_by_owner(db, current_user.id)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        repository = get_repository_by_id(db, repository_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repository


@router.post("/{repository_id}/sync", response_model=RepositoryResponse)
async def sync_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository or repository.owner_id != current_user.id:
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