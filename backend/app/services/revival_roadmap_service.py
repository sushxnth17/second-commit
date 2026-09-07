from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.revival_team import RevivalTeam
from app.models.revival_team_member import RevivalTeamMember
from app.models.revival_roadmap import RevivalRoadmapPhase, RevivalRoadmapTask
from app.models.user import User
from app.schemas.revival_roadmap import (
    RevivalRoadmapPhaseCreate,
    RevivalRoadmapPhaseUpdate,
    RevivalRoadmapPhaseResponse,
    RevivalRoadmapTaskCreate,
    RevivalRoadmapTaskUpdate,
    RevivalRoadmapTaskResponse,
    RevivalRoadmapResponse,
)


def _get_team_for_roadmap(
    db: Session,
    repository_id: int,
    current_user: User,
) -> tuple[Repository, RevivalTeam, bool, bool]:
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

    return repository, team, is_owner, is_member


def get_roadmap(
    db: Session,
    repository_id: int,
    current_user: User,
) -> RevivalRoadmapResponse:
    _, team, _, _ = _get_team_for_roadmap(db, repository_id, current_user)

    phases = (
        db.query(RevivalRoadmapPhase)
        .filter(RevivalRoadmapPhase.team_id == team.id)
        .order_by(RevivalRoadmapPhase.position.asc(), RevivalRoadmapPhase.id.asc())
        .all()
    )

    phase_responses = []
    for phase in phases:
        sorted_tasks = sorted(phase.tasks, key=lambda t: (t.position, t.id))
        phase_responses.append(
            RevivalRoadmapPhaseResponse(
                id=phase.id,
                title=phase.title,
                description=phase.description,
                position=phase.position,
                tasks=[RevivalRoadmapTaskResponse.model_validate(t) for t in sorted_tasks],
                created_at=phase.created_at,
                updated_at=phase.updated_at,
            )
        )

    return RevivalRoadmapResponse(phases=phase_responses)


def create_phase(
    db: Session,
    repository_id: int,
    phase_in: RevivalRoadmapPhaseCreate,
    current_user: User,
) -> RevivalRoadmapPhase:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    if not is_owner:
        raise HTTPException(status_code=404, detail="Repository not found")

    if phase_in.position is None:
        max_pos = (
            db.query(func.max(RevivalRoadmapPhase.position))
            .filter(RevivalRoadmapPhase.team_id == team.id)
            .scalar()
        )
        position = (max_pos + 1) if max_pos is not None else 0
    else:
        position = phase_in.position

    try:
        phase = RevivalRoadmapPhase(
            team_id=team.id,
            title=phase_in.title,
            description=phase_in.description,
            position=position,
        )
        db.add(phase)
        db.commit()
        db.refresh(phase)
        return phase
    except Exception:
        db.rollback()
        raise


def update_phase(
    db: Session,
    repository_id: int,
    phase_id: int,
    phase_in: RevivalRoadmapPhaseUpdate,
    current_user: User,
) -> RevivalRoadmapPhase:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    if not is_owner:
        raise HTTPException(status_code=404, detail="Repository not found")

    phase = (
        db.query(RevivalRoadmapPhase)
        .filter(
            RevivalRoadmapPhase.id == phase_id,
            RevivalRoadmapPhase.team_id == team.id,
        )
        .first()
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Roadmap phase not found")

    update_data = phase_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    if "title" in update_data:
        phase.title = phase_in.title
    if "description" in update_data:
        phase.description = phase_in.description
    if "position" in update_data:
        phase.position = phase_in.position

    phase.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(phase)
        return phase
    except Exception:
        db.rollback()
        raise


def delete_phase(
    db: Session,
    repository_id: int,
    phase_id: int,
    current_user: User,
) -> None:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    if not is_owner:
        raise HTTPException(status_code=404, detail="Repository not found")

    phase = (
        db.query(RevivalRoadmapPhase)
        .filter(
            RevivalRoadmapPhase.id == phase_id,
            RevivalRoadmapPhase.team_id == team.id,
        )
        .first()
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Roadmap phase not found")

    try:
        db.delete(phase)
        db.commit()
    except Exception:
        db.rollback()
        raise


def create_task(
    db: Session,
    repository_id: int,
    phase_id: int,
    task_in: RevivalRoadmapTaskCreate,
    current_user: User,
) -> RevivalRoadmapTask:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    if not is_owner:
        raise HTTPException(status_code=404, detail="Repository not found")

    phase = (
        db.query(RevivalRoadmapPhase)
        .filter(
            RevivalRoadmapPhase.id == phase_id,
            RevivalRoadmapPhase.team_id == team.id,
        )
        .first()
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Roadmap phase not found")

    if task_in.position is None:
        max_pos = (
            db.query(func.max(RevivalRoadmapTask.position))
            .filter(RevivalRoadmapTask.phase_id == phase.id)
            .scalar()
        )
        position = (max_pos + 1) if max_pos is not None else 0
    else:
        position = task_in.position

    try:
        task = RevivalRoadmapTask(
            phase_id=phase.id,
            title=task_in.title,
            description=task_in.description,
            position=position,
            status="todo",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def update_task(
    db: Session,
    repository_id: int,
    phase_id: int,
    task_id: int,
    task_in: RevivalRoadmapTaskUpdate,
    current_user: User,
) -> RevivalRoadmapTask:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    phase = (
        db.query(RevivalRoadmapPhase)
        .filter(
            RevivalRoadmapPhase.id == phase_id,
            RevivalRoadmapPhase.team_id == team.id,
        )
        .first()
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Roadmap phase not found")

    task = (
        db.query(RevivalRoadmapTask)
        .filter(
            RevivalRoadmapTask.id == task_id,
            RevivalRoadmapTask.phase_id == phase.id,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Roadmap task not found")

    update_data = task_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    if not is_owner:
        disallowed_fields = set(update_data.keys()) - {"status"}
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members are only permitted to update status",
            )

    if is_owner:
        if "title" in update_data:
            task.title = task_in.title
        if "description" in update_data:
            task.description = task_in.description
        if "position" in update_data:
            task.position = task_in.position

    if "status" in update_data:
        task.status = task_in.status

    task.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def delete_task(
    db: Session,
    repository_id: int,
    phase_id: int,
    task_id: int,
    current_user: User,
) -> None:
    _, team, is_owner, _ = _get_team_for_roadmap(db, repository_id, current_user)

    if not is_owner:
        raise HTTPException(status_code=404, detail="Repository not found")

    phase = (
        db.query(RevivalRoadmapPhase)
        .filter(
            RevivalRoadmapPhase.id == phase_id,
            RevivalRoadmapPhase.team_id == team.id,
        )
        .first()
    )
    if not phase:
        raise HTTPException(status_code=404, detail="Roadmap phase not found")

    task = (
        db.query(RevivalRoadmapTask)
        .filter(
            RevivalRoadmapTask.id == task_id,
            RevivalRoadmapTask.phase_id == phase.id,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Roadmap task not found")

    try:
        db.delete(task)
        db.commit()
    except Exception:
        db.rollback()
        raise
