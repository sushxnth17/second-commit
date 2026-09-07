import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.repository import Repository
from app.models.revival_team import RevivalTeam
from app.models.revival_team_member import RevivalTeamMember
from app.models.revival_roadmap import RevivalRoadmapPhase, RevivalRoadmapTask
from app.models.user import User
from app.services.repository_service import create_repository
from app.services.user_service import create_user


# ==============================================================================
# 1. PERSISTENCE TESTS
# ==============================================================================

def test_1_phase_creation(db_session, test_user, test_repo):
    """1. Phase can be created and persisted for a revival team."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(
        team_id=team.id,
        title="Phase 1: Foundation",
        description="Core architecture setup",
        position=0,
    )
    db_session.add(phase)
    db_session.commit()
    db_session.refresh(phase)

    assert phase.id is not None
    assert phase.team_id == team.id
    assert phase.title == "Phase 1: Foundation"
    assert phase.description == "Core architecture setup"
    assert phase.position == 0
    assert phase.created_at is not None
    assert phase.updated_at is not None


def test_2_task_creation(db_session, test_user, test_repo):
    """2. Task can be created and persisted for a roadmap phase."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(
        team_id=team.id,
        title="Phase 1: Foundation",
        position=0,
    )
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(
        phase_id=phase.id,
        title="Set up database migrations",
        description="Add Alembic support",
        position=0,
        status="todo",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.phase_id == phase.id
    assert task.title == "Set up database migrations"
    assert task.status == "todo"
    assert task.created_at is not None
    assert task.updated_at is not None


def test_3_phase_task_relationship(db_session, test_user, test_repo):
    """3. Phase -> task relationship functions bidirectionally."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(
        team_id=team.id,
        title="Phase 1: Foundation",
    )
    db_session.add(phase)
    db_session.commit()

    task1 = RevivalRoadmapTask(phase_id=phase.id, title="Task One")
    task2 = RevivalRoadmapTask(phase_id=phase.id, title="Task Two")
    db_session.add_all([task1, task2])
    db_session.commit()

    db_session.refresh(phase)
    assert len(phase.tasks) == 2
    assert task1.phase.id == phase.id
    assert task2.phase.id == phase.id


def test_4_deterministic_phase_ordering(db_session, test_user, test_repo):
    """4. Deterministic phase ordering: position ASC, id ASC."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    p3 = RevivalRoadmapPhase(team_id=team.id, title="P3", position=2)
    p1 = RevivalRoadmapPhase(team_id=team.id, title="P1", position=0)
    p2 = RevivalRoadmapPhase(team_id=team.id, title="P2", position=1)
    p1_tie = RevivalRoadmapPhase(team_id=team.id, title="P1 Tie", position=0)
    db_session.add_all([p3, p1, p2, p1_tie])
    db_session.commit()

    phases = (
        db_session.query(RevivalRoadmapPhase)
        .filter_by(team_id=team.id)
        .order_by(RevivalRoadmapPhase.position.asc(), RevivalRoadmapPhase.id.asc())
        .all()
    )
    assert [p.title for p in phases] == ["P1", "P1 Tie", "P2", "P3"]


def test_5_deterministic_task_ordering(db_session, test_user, test_repo):
    """5. Deterministic task ordering: position ASC, id ASC."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1", position=0)
    db_session.add(phase)
    db_session.commit()

    t3 = RevivalRoadmapTask(phase_id=phase.id, title="T3", position=5)
    t1 = RevivalRoadmapTask(phase_id=phase.id, title="T1", position=0)
    t2 = RevivalRoadmapTask(phase_id=phase.id, title="T2", position=2)
    t1_tie = RevivalRoadmapTask(phase_id=phase.id, title="T1 Tie", position=0)
    db_session.add_all([t3, t1, t2, t1_tie])
    db_session.commit()

    tasks = (
        db_session.query(RevivalRoadmapTask)
        .filter_by(phase_id=phase.id)
        .order_by(RevivalRoadmapTask.position.asc(), RevivalRoadmapTask.id.asc())
        .all()
    )
    assert [t.title for t in tasks] == ["T1", "T1 Tie", "T2", "T3"]


def test_6_cascade_deleting_phase_deletes_tasks(db_session, test_user, test_repo):
    """6. Cascade deleting a phase deletes its tasks."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task1 = RevivalRoadmapTask(phase_id=phase.id, title="T1")
    task2 = RevivalRoadmapTask(phase_id=phase.id, title="T2")
    db_session.add_all([task1, task2])
    db_session.commit()

    phase_id = phase.id
    task1_id = task1.id
    task2_id = task2.id

    db_session.delete(phase)
    db_session.commit()

    assert db_session.query(RevivalRoadmapPhase).filter_by(id=phase_id).first() is None
    assert db_session.query(RevivalRoadmapTask).filter_by(id=task1_id).first() is None
    assert db_session.query(RevivalRoadmapTask).filter_by(id=task2_id).first() is None


def test_7_deleting_revival_team_deletes_phases_and_tasks(db_session, test_user, test_repo):
    """7. Deleting a revival team deletes phases and tasks."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1")
    db_session.add(task)
    db_session.commit()

    team_id = team.id
    phase_id = phase.id
    task_id = task.id

    db_session.delete(team)
    db_session.commit()

    assert db_session.query(RevivalTeam).filter_by(id=team_id).first() is None
    assert db_session.query(RevivalRoadmapPhase).filter_by(id=phase_id).first() is None
    assert db_session.query(RevivalRoadmapTask).filter_by(id=task_id).first() is None


# ==============================================================================
# 2. AUTHORIZATION TESTS
# ==============================================================================

def test_8_unauthenticated_get_denied(client, db_session, test_user, test_repo, auth_context):
    """8. Unauthenticated GET denied with 401."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = None
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 401


def test_9_team_owner_can_view_roadmap(client, db_session, test_user, test_repo, auth_context):
    """9. Team owner can view roadmap."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1")
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 200
    data = res.json()
    assert "phases" in data
    assert len(data["phases"]) == 1
    assert data["phases"][0]["title"] == "Phase 1"
    assert len(data["phases"][0]["tasks"]) == 1
    assert data["phases"][0]["tasks"][0]["title"] == "T1"


def test_10_active_member_can_view_roadmap(client, db_session, test_user, test_repo, auth_context):
    """10. Active member can view roadmap."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92001,
        username="active_member",
        name="Active Member",
        avatar_url=None,
        access_token="tok_1",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    auth_context.user = member_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 200
    data = res.json()
    assert "phases" in data
    assert len(data["phases"]) == 1


def test_11_non_member_denied_even_when_repository_is_published(client, db_session, test_user, test_repo, auth_context):
    """11. Non-member denied even when repository is published."""
    test_repo.published = True
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=92002,
        username="outsider",
        name="Outsider",
        avatar_url=None,
        access_token="tok_2",
    )

    auth_context.user = outsider
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_12_repository_owner_who_is_not_team_owner_or_member_denied(client, db_session, test_user, test_repo, auth_context):
    """12. Repository owner who is not team owner/member denied."""
    different_team_owner = create_user(
        db=db_session,
        github_id=92003,
        username="team_lead",
        name="Team Lead",
        avatar_url=None,
        access_token="tok_3",
    )
    # test_repo.owner_id is test_user.id
    team = RevivalTeam(repository_id=test_repo.id, owner_id=different_team_owner.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_13_non_owner_member_cannot_create_phase(client, db_session, test_user, test_repo, auth_context):
    """13. Non-owner member cannot create phase."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92004,
        username="member_create_phase",
        name="Member",
        avatar_url=None,
        access_token="tok_4",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = member_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases",
        json={"title": "Member Phase"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"
    assert db_session.query(RevivalRoadmapPhase).filter_by(team_id=team.id).count() == 0


def test_14_non_owner_member_cannot_create_task(client, db_session, test_user, test_repo, auth_context):
    """14. Non-owner member cannot create task."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92005,
        username="member_create_task",
        name="Member",
        avatar_url=None,
        access_token="tok_5",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = member_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks",
        json={"title": "Member Task"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"
    assert db_session.query(RevivalRoadmapTask).filter_by(phase_id=phase.id).count() == 0


def test_15_non_owner_member_cannot_edit_phase(client, db_session, test_user, test_repo, auth_context):
    """15. Non-owner member cannot edit phase."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1", description="Original")
    db_session.add(phase)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92006,
        username="member_edit_phase",
        name="Member",
        avatar_url=None,
        access_token="tok_6",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = member_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={"title": "Hacked Phase"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"

    db_session.refresh(phase)
    assert phase.title == "Phase 1"


def test_16_non_owner_member_cannot_edit_task_fields_other_than_status(client, db_session, test_user, test_repo, auth_context):
    """16. Non-owner member cannot edit task fields other than status (403)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="Original Title", description="Original Desc", position=0, status="todo")
    db_session.add(task)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92007,
        username="member_edit_task_fields",
        name="Member",
        avatar_url=None,
        access_token="tok_7",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = member_user
    # Attempt updating title
    res1 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"title": "New Title"},
    )
    assert res1.status_code == 403
    assert "Members are only permitted to update status" in res1.json()["detail"]

    # Attempt updating description
    res2 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"description": "New Desc"},
    )
    assert res2.status_code == 403

    # Attempt updating position
    res3 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"position": 10},
    )
    assert res3.status_code == 403

    db_session.refresh(task)
    assert task.title == "Original Title"
    assert task.description == "Original Desc"
    assert task.position == 0


def test_17_non_owner_member_cannot_delete_phase_or_task(client, db_session, test_user, test_repo, auth_context):
    """17. Non-owner member cannot delete phase or task."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="Task 1")
    db_session.add(task)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92008,
        username="member_delete",
        name="Member",
        avatar_url=None,
        access_token="tok_8",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = member_user
    # Attempt delete phase
    res_phase = client.delete(f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}")
    assert res_phase.status_code == 404
    assert res_phase.json()["detail"] == "Repository not found"

    # Attempt delete task
    res_task = client.delete(f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}")
    assert res_task.status_code == 404
    assert res_task.json()["detail"] == "Repository not found"

    assert db_session.query(RevivalRoadmapPhase).filter_by(id=phase.id).first() is not None
    assert db_session.query(RevivalRoadmapTask).filter_by(id=task.id).first() is not None


# ==============================================================================
# 3. VALIDATION TESTS
# ==============================================================================

def test_18_empty_phase_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """18. Empty phase title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases",
        json={"title": "   "},
    )
    assert res.status_code == 422


def test_19_empty_task_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """19. Empty task title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks",
        json={"title": ""},
    )
    assert res.status_code == 422


def test_20_title_length_over_200_rejected(client, db_session, test_user, test_repo, auth_context):
    """20. Title length > 200 rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    auth_context.user = test_user
    res_phase = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases",
        json={"title": "x" * 201},
    )
    assert res_phase.status_code == 422

    res_task = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks",
        json={"title": "y" * 201},
    )
    assert res_task.status_code == 422


def test_21_invalid_task_status_rejected(client, db_session, test_user, test_repo, auth_context):
    """21. Invalid task status rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1", status="todo")
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "in_review"},
    )
    assert res.status_code == 422


def test_22_empty_patch_rejected(client, db_session, test_user, test_repo, auth_context):
    """22. Empty PATCH rejected with 400."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1")
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user
    res_phase = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={},
    )
    assert res_phase.status_code == 400
    assert "No fields provided" in res_phase.json()["detail"]

    res_task = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={},
    )
    assert res_task.status_code == 400
    assert "No fields provided" in res_task.json()["detail"]


def test_23_task_creation_always_starts_as_todo(client, db_session, test_user, test_repo, auth_context):
    """23. Task creation always starts as 'todo', ignoring client attempts to set other initial status."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks",
        json={"title": "Client Status Tamper", "status": "completed"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "todo"

    task = db_session.query(RevivalRoadmapTask).filter_by(id=data["id"]).first()
    assert task.status == "todo"


# ==============================================================================
# 4. ISOLATION TESTS
# ==============================================================================

def test_24_phase_from_another_repository_returns_404(client, db_session, test_user, test_repo, auth_context):
    """24. Phase from another repository returns 404."""
    team1 = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team1)

    repo2 = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 99002,
            "name": "repo-two",
            "full_name": f"{test_user.username}/repo-two",
            "html_url": f"https://github.com/{test_user.username}/repo-two",
            "default_branch": "main",
        },
    )
    team2 = RevivalTeam(repository_id=repo2.id, owner_id=test_user.id)
    db_session.add(team2)
    db_session.commit()

    phase_team2 = RevivalRoadmapPhase(team_id=team2.id, title="Phase on Repo 2")
    db_session.add(phase_team2)
    db_session.commit()

    auth_context.user = test_user
    # Access phase of repo 2 via repo 1 endpoint
    res_patch = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase_team2.id}",
        json={"title": "Attempted Cross-Repo Update"},
    )
    assert res_patch.status_code == 404
    assert res_patch.json()["detail"] == "Roadmap phase not found"

    res_del = client.delete(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase_team2.id}",
    )
    assert res_del.status_code == 404
    assert res_del.json()["detail"] == "Roadmap phase not found"


def test_25_task_from_another_repository_returns_404(client, db_session, test_user, test_repo, auth_context):
    """25. Task from another repository returns 404."""
    team1 = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team1)
    db_session.commit()

    phase1 = RevivalRoadmapPhase(team_id=team1.id, title="Phase 1")
    db_session.add(phase1)
    db_session.commit()

    repo2 = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 99003,
            "name": "repo-three",
            "full_name": f"{test_user.username}/repo-three",
            "html_url": f"https://github.com/{test_user.username}/repo-three",
            "default_branch": "main",
        },
    )
    team2 = RevivalTeam(repository_id=repo2.id, owner_id=test_user.id)
    db_session.add(team2)
    db_session.commit()

    phase2 = RevivalRoadmapPhase(team_id=team2.id, title="Phase 2")
    db_session.add(phase2)
    db_session.commit()

    task2 = RevivalRoadmapTask(phase_id=phase2.id, title="Task on Repo 2")
    db_session.add(task2)
    db_session.commit()

    auth_context.user = test_user
    # Attempt patching task2 via repo1
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase1.id}/tasks/{task2.id}",
        json={"status": "in_progress"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Roadmap task not found"


def test_26_task_from_another_phase_returns_404(client, db_session, test_user, test_repo, auth_context):
    """26. Task from another phase in the same repository returns 404."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase1 = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    phase2 = RevivalRoadmapPhase(team_id=team.id, title="Phase 2")
    db_session.add_all([phase1, phase2])
    db_session.commit()

    task_in_phase2 = RevivalRoadmapTask(phase_id=phase2.id, title="Task in Phase 2")
    db_session.add(task_in_phase2)
    db_session.commit()

    auth_context.user = test_user
    # Target phase1 route with task belonging to phase2
    res_patch = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase1.id}/tasks/{task_in_phase2.id}",
        json={"status": "completed"},
    )
    assert res_patch.status_code == 404
    assert res_patch.json()["detail"] == "Roadmap task not found"

    res_del = client.delete(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase1.id}/tasks/{task_in_phase2.id}",
    )
    assert res_del.status_code == 404
    assert res_del.json()["detail"] == "Roadmap task not found"


# ==============================================================================
# 5. LIFECYCLE TESTS
# ==============================================================================

def test_27_member_can_change_task_status_lifecycle(client, db_session, test_user, test_repo, auth_context):
    """27. Member can change task status todo -> in_progress -> completed."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92009,
        username="lifecycle_dev",
        name="Lifecycle Dev",
        avatar_url=None,
        access_token="tok_9",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1", status="todo")
    db_session.add(task)
    db_session.commit()

    auth_context.user = member_user

    # Step 1: todo -> in_progress
    res1 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "in_progress"},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "in_progress"

    # Step 2: in_progress -> completed
    res2 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "completed"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "completed"

    db_session.refresh(task)
    assert task.status == "completed"


def test_28_owner_can_change_task_status(client, db_session, test_user, test_repo, auth_context):
    """28. Owner can change task status."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1", status="todo")
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "completed", "title": "Updated Title By Owner"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    assert res.json()["title"] == "Updated Title By Owner"

    db_session.refresh(task)
    assert task.status == "completed"
    assert task.title == "Updated Title By Owner"


def test_29_member_removal_does_not_delete_roadmap_data(client, db_session, test_user, test_repo, auth_context):
    """29. Member removal does not delete roadmap data."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92010,
        username="leaving_member",
        name="Leaving Member",
        avatar_url=None,
        access_token="tok_10",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    phase = RevivalRoadmapPhase(team_id=team.id, title="Important Phase")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="Important Task")
    db_session.add(task)
    db_session.commit()

    # Owner removes member
    auth_context.user = test_user
    del_res = client.delete(f"/repositories/{test_repo.id}/revival-team/members/{member_user.id}")
    assert del_res.status_code == 204

    # Verify roadmap data persists completely
    db_session.refresh(phase)
    db_session.refresh(task)
    assert phase.id is not None
    assert task.id is not None
    assert len(phase.tasks) == 1


def test_30_member_who_leaves_can_no_longer_access_or_update_roadmap(client, db_session, test_user, test_repo, auth_context):
    """30. Member who leaves can no longer access/update roadmap."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=92011,
        username="departing_member",
        name="Departing Member",
        avatar_url=None,
        access_token="tok_11",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1")
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="T1", status="todo")
    db_session.add(task)
    db_session.commit()

    # Member leaves team
    auth_context.user = member_user
    leave_res = client.delete(f"/repositories/{test_repo.id}/revival-team/members/me")
    assert leave_res.status_code == 204

    # Subsequent GET roadmap -> 404
    get_res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Repository not found"

    # Subsequent PATCH task -> 404
    patch_res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "in_progress"},
    )
    assert patch_res.status_code == 404
    assert patch_res.json()["detail"] == "Repository not found"


def test_31_published_repository_remains_private_to_non_team_members(client, db_session, test_user, test_repo, auth_context):
    """31. Published repository remains private to non-team members."""
    test_repo.published = True
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Confidential Roadmap")
    db_session.add(phase)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=92012,
        username="public_visitor",
        name="Public Visitor",
        avatar_url=None,
        access_token="tok_12",
    )

    auth_context.user = outsider
    res = client.get(f"/repositories/{test_repo.id}/revival-team/roadmap")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


# ==============================================================================
# 6. TIMESTAMP TESTS
# ==============================================================================

def test_32_successful_update_changes_updated_at(client, db_session, test_user, test_repo, auth_context):
    """32. Successful update changes updated_at."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    past_time = datetime.utcnow() - timedelta(hours=2)
    phase = RevivalRoadmapPhase(
        team_id=team.id,
        title="Phase 1",
        created_at=past_time,
        updated_at=past_time,
    )
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(
        phase_id=phase.id,
        title="T1",
        created_at=past_time,
        updated_at=past_time,
    )
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user
    # Update phase
    res_phase = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={"title": "Updated Phase Title"},
    )
    assert res_phase.status_code == 200
    db_session.refresh(phase)
    assert phase.updated_at > past_time

    # Update task
    res_task = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"title": "Updated Task Title"},
    )
    assert res_task.status_code == 200
    db_session.refresh(task)
    assert task.updated_at > past_time


def test_33_failed_update_does_not_modify_updated_at(client, db_session, test_user, test_repo, auth_context):
    """33. Failed update does not modify updated_at."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    fixed_time = datetime(2026, 1, 1, 12, 0, 0)
    phase = RevivalRoadmapPhase(
        team_id=team.id,
        title="Phase Fixed",
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(
        phase_id=phase.id,
        title="Task Fixed",
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user

    # Failed phase update (empty payload -> 400)
    res_phase_empty = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={},
    )
    assert res_phase_empty.status_code == 400
    db_session.refresh(phase)
    assert phase.updated_at == fixed_time

    # Failed task update (invalid status -> 422)
    res_task_invalid = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"status": "invalid_status"},
    )
    assert res_task_invalid.status_code == 422
    db_session.refresh(task)
    assert task.updated_at == fixed_time


# ==============================================================================
# 7. POSITION AUTO-PLACEMENT TESTS
# ==============================================================================

def test_34_omitted_position_places_after_last_phase_and_task(client, db_session, test_user, test_repo, auth_context):
    """34. Omitted position places after current last phase and task."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user

    # Phase 1 without position -> should be position 0
    res_p1 = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases",
        json={"title": "First Phase"},
    )
    assert res_p1.status_code == 201
    assert res_p1.json()["position"] == 0
    p1_id = res_p1.json()["id"]

    # Phase 2 without position -> should be position 1
    res_p2 = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases",
        json={"title": "Second Phase"},
    )
    assert res_p2.status_code == 201
    assert res_p2.json()["position"] == 1

    # Task 1 in Phase 1 without position -> should be position 0
    res_t1 = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{p1_id}/tasks",
        json={"title": "Task One"},
    )
    assert res_t1.status_code == 201
    assert res_t1.json()["position"] == 0

    # Task 2 in Phase 1 without position -> should be position 1
    res_t2 = client.post(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{p1_id}/tasks",
        json={"title": "Task Two"},
    )
    assert res_t2.status_code == 201
    assert res_t2.json()["position"] == 1


# ==============================================================================
# 8. POSITION NULL VALIDATION TESTS (PATCH)
# ==============================================================================

def test_35_patch_phase_position_handling(client, db_session, test_user, test_repo, auth_context):
    """35. PATCH phase position handling: omitted succeeds, valid integer succeeds, null returns 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1", position=0)
    db_session.add(phase)
    db_session.commit()

    auth_context.user = test_user

    # 1. PATCH without position succeeds
    res_no_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={"title": "Phase Renamed"},
    )
    assert res_no_pos.status_code == 200
    assert res_no_pos.json()["title"] == "Phase Renamed"
    assert res_no_pos.json()["position"] == 0

    # 2. PATCH with a valid integer position succeeds
    res_valid_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={"position": 5},
    )
    assert res_valid_pos.status_code == 200
    assert res_valid_pos.json()["position"] == 5

    # 3. PATCH with "position": null returns 422
    res_null_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}",
        json={"position": None},
    )
    assert res_null_pos.status_code == 422


def test_36_patch_task_position_handling(client, db_session, test_user, test_repo, auth_context):
    """36. PATCH task position handling: omitted succeeds, valid integer succeeds, null returns 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    phase = RevivalRoadmapPhase(team_id=team.id, title="Phase 1", position=0)
    db_session.add(phase)
    db_session.commit()

    task = RevivalRoadmapTask(phase_id=phase.id, title="Task 1", position=0)
    db_session.add(task)
    db_session.commit()

    auth_context.user = test_user

    # 1. PATCH without position succeeds
    res_no_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"title": "Task Renamed"},
    )
    assert res_no_pos.status_code == 200
    assert res_no_pos.json()["title"] == "Task Renamed"
    assert res_no_pos.json()["position"] == 0

    # 2. PATCH with a valid integer position succeeds
    res_valid_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"position": 7},
    )
    assert res_valid_pos.status_code == 200
    assert res_valid_pos.json()["position"] == 7

    # 3. PATCH with "position": null returns 422
    res_null_pos = client.patch(
        f"/repositories/{test_repo.id}/revival-team/roadmap/phases/{phase.id}/tasks/{task.id}",
        json={"position": None},
    )
    assert res_null_pos.status_code == 422
