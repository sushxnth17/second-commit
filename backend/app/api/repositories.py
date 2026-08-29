from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.revival_brief import RevivalBrief
from app.schemas.repository import RepositoryResponse
from app.schemas.dashboard import RepositorySummary
from app.schemas.revival_brief import RevivalBriefResponse, RevivalBriefUpdate
from app.services.repository_service import (
    get_repository_by_github_id,
    create_repository,
    get_repositories_by_owner,
    update_repository,
    get_repository_by_id,
)
from app.services.github_service import get_user_repositories, get_repository_details
from app.services.health_service import get_health
from app.services.dormancy_service import get_repository_dormancy


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
        if existing.owner_id == current_user.id:
            return {
                "message": "Repository already imported",
                "repository": {
                    "id": existing.id,
                    "name": existing.name,
                },
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Repository is already associated with another account.",
            )

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


@router.get("/discover", response_model=list[RepositoryResponse])
async def discover_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all published repositories.
    Sorted by ID descending (newest first).
    """
    repositories = (
        db.query(Repository)
        .filter(Repository.published == True)
        .order_by(Repository.id.desc())
        .all()
    )
    return repositories


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

    if repository.owner_id != current_user.id and not repository.published:
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
        status_code = e.response.status_code
        if status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="GitHub authentication token is invalid or has expired.",
            )
        elif status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="Access to the GitHub repository is forbidden (rate limit or permissions issue).",
            )
        elif status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="The GitHub repository was not found or is unavailable.",
            )
        elif status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail="GitHub service is temporarily unavailable. Please try again later.",
            )
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to sync with GitHub (HTTP {status_code}).",
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to the GitHub API. Please check your network connection.",
        )

    updated_repository = update_repository(
        db=db,
        db_repo=repository,
        repo_data=github_data,
    )

    return updated_repository


@router.post("/{repository_id}/publish", response_model=RepositoryResponse)
async def publish_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Repository owned by another user",
        )

    repository.published = True
    db.commit()
    db.refresh(repository)

    return repository


@router.post("/{repository_id}/unpublish", response_model=RepositoryResponse)
async def unpublish_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Repository owned by another user",
        )

    repository.published = False
    db.commit()
    db.refresh(repository)

    return repository


@router.get("/{repository_id}/handover", response_model=RevivalBriefResponse | None)
async def get_repository_handover(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current Revival Brief for the repository.
    Owners can read it anytime.
    Other authenticated users can read it only if the repository is published.
    """
    try:
        repository = get_repository_by_id(db, repository_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repository.owner_id != current_user.id and not repository.published:
        raise HTTPException(status_code=404, detail="Repository not found")

    brief = db.query(RevivalBrief).filter(RevivalBrief.repository_id == repository_id).first()
    return brief


@router.put("/{repository_id}/handover", response_model=RevivalBriefResponse)
async def update_repository_handover(
    repository_id: int,
    payload: RevivalBriefUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update the Revival Brief. Only the owner can do this.
    """
    try:
        repository = get_repository_by_id(db, repository_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    brief = db.query(RevivalBrief).filter(RevivalBrief.repository_id == repository_id).first()
    if not brief:
        brief = RevivalBrief(
            repository_id=repository_id,
            developer_notes=payload.developer_notes if payload.developer_notes is not None else "",
            revival_intent=payload.revival_intent if payload.revival_intent is not None else "",
            status=payload.status if payload.status is not None else "draft",
        )
        db.add(brief)
    else:
        if payload.developer_notes is not None:
            brief.developer_notes = payload.developer_notes
        if payload.revival_intent is not None:
            brief.revival_intent = payload.revival_intent
        if payload.status is not None:
            brief.status = payload.status

    db.commit()
    db.refresh(brief)
    return brief


@router.delete("/{repository_id}/handover")
async def delete_repository_handover(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset/delete the Revival Brief. Only the owner can do this.
    """
    try:
        repository = get_repository_by_id(db, repository_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    brief = db.query(RevivalBrief).filter(RevivalBrief.repository_id == repository_id).first()
    if brief:
        db.delete(brief)
        db.commit()
    return {"status": "success"}