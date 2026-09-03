from fastapi import APIRouter, Depends, HTTPException, Response, status
import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.revival_brief import RevivalBrief
from app.models.revival_request import RevivalRequest
from app.models.revival_team import RevivalTeam
from app.models.revival_team_member import RevivalTeamMember
from app.models.revival_work_item import RevivalWorkItem
from app.schemas.repository import RepositoryResponse
from app.schemas.dashboard import RepositorySummary
from app.schemas.revival_brief import RevivalBriefResponse, RevivalBriefUpdate
from app.schemas.revival_request import RevivalRequestCreate, RevivalRequestResponse
from app.schemas.revival_team import RevivalTeamResponse, TeamUserSummary, RevivalTeamMemberResponse
from app.schemas.revival_work_item import RevivalWorkItemCreate, RevivalWorkItemResponse

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


@router.post("/{repository_id}/revival-requests", response_model=RevivalRequestResponse, status_code=201)
async def create_revival_request(
    repository_id: int,
    payload: RevivalRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    if not repository.published and repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    if repository.owner_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot request to revive your own repository.",
        )

    existing_request = (
        db.query(RevivalRequest)
        .filter(
            RevivalRequest.repository_id == repository_id,
            RevivalRequest.requester_id == current_user.id,
            RevivalRequest.status == "pending",
        )
        .first()
    )
    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="You already have an active pending revival request for this repository.",
        )

    new_request = RevivalRequest(
        repository_id=repository_id,
        requester_id=current_user.id,
        message=payload.message,
        status="pending",
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


@router.get("/{repository_id}/revival-requests/my-pending", response_model=RevivalRequestResponse | None)
async def get_my_pending_revival_request(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    if not repository.published and repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    request = (
        db.query(RevivalRequest)
        .filter(
            RevivalRequest.repository_id == repository_id,
            RevivalRequest.requester_id == current_user.id,
            RevivalRequest.status == "pending",
        )
        .first()
    )
    return request


@router.get("/{repository_id}/revival-requests", response_model=list[RevivalRequestResponse])
async def list_revival_requests(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    if repository.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    requests = (
        db.query(RevivalRequest)
        .filter(RevivalRequest.repository_id == repository_id)
        .order_by(RevivalRequest.created_at.desc())
        .all()
    )
    return requests


@router.get("/{repository_id}/revival-requests/my", response_model=RevivalRequestResponse | None)
async def get_my_revival_request(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    request = (
        db.query(RevivalRequest)
        .filter(
            RevivalRequest.repository_id == repository_id,
            RevivalRequest.requester_id == current_user.id,
        )
        .order_by(RevivalRequest.created_at.desc())
        .first()
    )

    if not repository.published and repository.owner_id != current_user.id and not request:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return request


@router.post("/{repository_id}/revival-requests/{request_id}/approve", response_model=RevivalRequestResponse)
async def approve_revival_request(
    repository_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")

    request = db.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    if not request or request.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Revival request not found")

    if request.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Revival request has already been decided.",
        )

    try:
        team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()
        if not team:
            team = RevivalTeam(
                repository_id=repository.id,
                owner_id=repository.owner_id,
            )
            db.add(team)
            db.flush()

        existing_member = (
            db.query(RevivalTeamMember)
            .filter(
                RevivalTeamMember.team_id == team.id,
                RevivalTeamMember.user_id == request.requester_id,
            )
            .first()
        )
        if not existing_member:
            new_member = RevivalTeamMember(
                team_id=team.id,
                user_id=request.requester_id,
            )
            db.add(new_member)

        request.status = "approved"
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not approve request due to a conflict.",
        )
    except Exception:
        db.rollback()
        raise

    db.refresh(request)
    return request


@router.post("/{repository_id}/revival-requests/{request_id}/reject", response_model=RevivalRequestResponse)
async def reject_revival_request(
    repository_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repository.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")

    request = db.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    if not request or request.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Revival request not found")

    if request.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Revival request has already been decided.",
        )

    request.status = "rejected"
    db.commit()
    db.refresh(request)
    return request


@router.get("/{repository_id}/revival-team", response_model=RevivalTeamResponse)
async def get_revival_team(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()

    is_owner = repository.owner_id == current_user.id
    is_published = repository.published
    is_member = False
    if team:
        is_member = (
            db.query(RevivalTeamMember)
            .filter(
                RevivalTeamMember.team_id == team.id,
                RevivalTeamMember.user_id == current_user.id,
            )
            .first()
            is not None
        )

    if not is_owner and not is_published and not is_member:
        raise HTTPException(status_code=404, detail="Repository not found")

    if not team:
        raise HTTPException(status_code=404, detail="Revival team not found")

    members = (
        db.query(RevivalTeamMember)
        .filter(RevivalTeamMember.team_id == team.id)
        .order_by(RevivalTeamMember.joined_at.asc(), RevivalTeamMember.id.asc())
        .all()
    )

    return RevivalTeamResponse(
        id=team.id,
        repository_id=team.repository_id,
        owner_id=team.owner_id,
        created_at=team.created_at,
        updated_at=team.updated_at,
        owner=TeamUserSummary.model_validate(team.owner) if team.owner else None,
        members=[RevivalTeamMemberResponse.model_validate(m) for m in members],
    )


@router.delete(
    "/{repository_id}/revival-team/members/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_revival_team(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()

    is_owner = repository.owner_id == current_user.id
    is_published = repository.published

    if not team:
        if not is_owner and not is_published:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=404, detail="Revival team not found")

    if team.owner_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Team owner cannot leave the revival team.",
        )

    member = (
        db.query(RevivalTeamMember)
        .filter(
            RevivalTeamMember.team_id == team.id,
            RevivalTeamMember.user_id == current_user.id,
        )
        .first()
    )

    if not member:
        if not is_owner and not is_published:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=404, detail="Team member not found")

    try:
        db.delete(member)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{repository_id}/revival-team/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_revival_team_member(
    repository_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()

    if not team:
        if not repository.published and repository.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=404, detail="Revival team not found")

    # Authoritative RevivalTeam.owner_id check
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")

    if user_id == team.owner_id:
        raise HTTPException(
            status_code=400,
            detail="Team owner cannot be removed from the revival team.",
        )

    member = (
        db.query(RevivalTeamMember)
        .filter(
            RevivalTeamMember.team_id == team.id,
            RevivalTeamMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    try:
        db.delete(member)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{repository_id}/revival-team/work-items",
    response_model=list[RevivalWorkItemResponse],
)
async def list_revival_work_items(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()
    if not team:
        if not repository.published and repository.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=404, detail="Revival team not found")

    is_owner = team.owner_id == current_user.id
    is_member = (
        db.query(RevivalTeamMember)
        .filter(
            RevivalTeamMember.team_id == team.id,
            RevivalTeamMember.user_id == current_user.id,
        )
        .first()
        is not None
    )

    if not is_owner and not is_member:
        raise HTTPException(status_code=404, detail="Repository not found")

    work_items = (
        db.query(RevivalWorkItem)
        .filter(RevivalWorkItem.team_id == team.id)
        .order_by(RevivalWorkItem.created_at.desc(), RevivalWorkItem.id.desc())
        .all()
    )

    return work_items


@router.post(
    "/{repository_id}/revival-team/work-items",
    response_model=RevivalWorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_revival_work_item(
    repository_id: int,
    item_in: RevivalWorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    team = db.query(RevivalTeam).filter(RevivalTeam.repository_id == repository_id).first()
    if not team:
        if not repository.published and repository.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(status_code=404, detail="Revival team not found")

    # Authoritative RevivalTeam.owner_id check
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Assignee validation if provided
    if item_in.assignee_id is not None:
        assignee_user = db.query(User).filter(User.id == item_in.assignee_id).first()
        if not assignee_user:
            raise HTTPException(status_code=404, detail="User not found")

        is_team_member = (
            assignee_user.id == team.owner_id
            or db.query(RevivalTeamMember)
            .filter(
                RevivalTeamMember.team_id == team.id,
                RevivalTeamMember.user_id == assignee_user.id,
            )
            .first()
            is not None
        )
        if not is_team_member:
            raise HTTPException(
                status_code=400,
                detail="Assignee must be an active member of the revival team.",
            )

    try:
        work_item = RevivalWorkItem(
            team_id=team.id,
            title=item_in.title,
            description=item_in.description,
            assignee_id=item_in.assignee_id,
            status="todo",
        )
        db.add(work_item)
        db.commit()
        db.refresh(work_item)
    except Exception:
        db.rollback()
        raise
    return work_item
