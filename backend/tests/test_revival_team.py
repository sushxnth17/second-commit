import pytest
from sqlalchemy.exc import IntegrityError

from app.models.repository import Repository
from app.models.revival_request import RevivalRequest
from app.models.revival_team import RevivalTeam
from app.models.revival_team_member import RevivalTeamMember
from app.models.user import User
from app.schemas.revival_team import RevivalTeamResponse, RevivalTeamMemberResponse
from app.services.repository_service import create_repository
from app.services.user_service import create_user


def test_create_revival_team(db_session, test_user, test_repo):
    """Verify RevivalTeam can be created and stores correct attributes."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    assert team.id is not None
    assert team.repository_id == test_repo.id
    assert team.owner_id == test_user.id
    assert team.created_at is not None
    assert team.updated_at is not None
    assert team.members == []


def test_repository_can_have_only_one_revival_team(db_session, test_user, test_repo):
    """Verify a repository can have at most one RevivalTeam."""
    team_1 = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team_1)
    db_session.commit()

    team_2 = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team_2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_revival_team_references_repository_and_owner(db_session, test_user, test_repo):
    """Verify RevivalTeam bidirectional relationships with Repository and User."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    # Team to repo and owner
    assert team.repository is not None
    assert team.repository.id == test_repo.id
    assert team.repository.name == test_repo.name

    assert team.owner is not None
    assert team.owner.id == test_user.id
    assert team.owner.username == test_user.username

    # Repo to team
    assert test_repo.revival_team is not None
    assert test_repo.revival_team.id == team.id

    # Owner to team
    assert team in test_user.owned_revival_teams


def test_create_revival_team_member(db_session, test_user, test_repo):
    """Verify RevivalTeamMember can be created and references user and team."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    developer_b = create_user(
        db=db_session,
        github_id=88888,
        username="dev_member",
        name="Dev Member",
        avatar_url="https://avatar.url/member",
        access_token="secret_token_123",
    )
    db_session.commit()

    member = RevivalTeamMember(
        team_id=team.id,
        user_id=developer_b.id,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    assert member.id is not None
    assert member.team_id == team.id
    assert member.user_id == developer_b.id
    assert member.joined_at is not None

    # Relationship verification
    assert member.team.id == team.id
    assert member.user.id == developer_b.id
    assert member.user.username == "dev_member"

    # Back-populates
    db_session.refresh(team)
    assert len(team.members) == 1
    assert team.members[0].id == member.id

    assert member in developer_b.revival_team_memberships


def test_duplicate_team_membership_is_prevented(db_session, test_user, test_repo):
    """Verify duplicate membership of the same user in the same team raises IntegrityError."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    developer_b = create_user(
        db=db_session,
        github_id=88889,
        username="dev_dupe",
        name="Dev Dupe",
        avatar_url="https://avatar.url/dupe",
        access_token="token_dupe",
    )
    db_session.commit()

    member_1 = RevivalTeamMember(
        team_id=team.id,
        user_id=developer_b.id,
    )
    db_session.add(member_1)
    db_session.commit()

    member_2 = RevivalTeamMember(
        team_id=team.id,
        user_id=developer_b.id,
    )
    db_session.add(member_2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_multiple_different_users_can_belong_to_same_team(db_session, test_user, test_repo):
    """Verify multiple distinct developers can be members of the same team."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    dev_1 = create_user(
        db=db_session,
        github_id=77701,
        username="dev_one",
        name="Dev One",
        avatar_url="https://avatar.url/1",
        access_token="tok_1",
    )
    dev_2 = create_user(
        db=db_session,
        github_id=77702,
        username="dev_two",
        name="Dev Two",
        avatar_url="https://avatar.url/2",
        access_token="tok_2",
    )
    db_session.commit()

    m1 = RevivalTeamMember(team_id=team.id, user_id=dev_1.id)
    m2 = RevivalTeamMember(team_id=team.id, user_id=dev_2.id)
    db_session.add_all([m1, m2])
    db_session.commit()

    db_session.refresh(team)
    assert len(team.members) == 2
    member_user_ids = {m.user_id for m in team.members}
    assert member_user_ids == {dev_1.id, dev_2.id}


def test_delete_team_cascades_to_memberships(db_session, test_user, test_repo):
    """Verify deleting a team removes all associated team memberships."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=66601,
        username="dev_cascade",
        name="Dev Cascade",
        avatar_url="https://avatar.url/c",
        access_token="tok_c",
    )
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    team_id = team.id
    member_id = member.id

    # Delete team
    db_session.delete(team)
    db_session.commit()

    assert db_session.query(RevivalTeam).filter(RevivalTeam.id == team_id).first() is None
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.id == member_id).first() is None
    # User dev should still exist
    assert db_session.query(User).filter(User.id == dev.id).first() is not None


def test_delete_repository_cascades_to_team_and_members(db_session, test_user, test_repo):
    """Verify deleting a repository removes its RevivalTeam and all team members."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=55501,
        username="dev_repo_cascade",
        name="Dev Repo Cascade",
        avatar_url="https://avatar.url/rc",
        access_token="tok_rc",
    )
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    repo_id = test_repo.id
    team_id = team.id
    member_id = member.id

    # Delete repository
    db_session.delete(test_repo)
    db_session.commit()

    assert db_session.query(Repository).filter(Repository.id == repo_id).first() is None
    assert db_session.query(RevivalTeam).filter(RevivalTeam.id == team_id).first() is None
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.id == member_id).first() is None
    # Test user and dev user still exist
    assert db_session.query(User).filter(User.id == test_user.id).first() is not None
    assert db_session.query(User).filter(User.id == dev.id).first() is not None


def test_delete_user_cascades_to_owned_team_and_memberships(db_session):
    """Verify deleting a user cascades to their owned teams and their memberships."""
    owner = create_user(
        db=db_session,
        github_id=44401,
        username="owner_user",
        name="Owner",
        avatar_url=None,
        access_token="tok_owner",
    )
    member_user = create_user(
        db=db_session,
        github_id=44402,
        username="member_user",
        name="Member",
        avatar_url=None,
        access_token="tok_member",
    )
    db_session.commit()

    repo = create_repository(
        db=db_session,
        owner_id=owner.id,
        repo={
            "id": 8801,
            "name": "repo-user-cascade",
            "full_name": "owner_user/repo-user-cascade",
            "html_url": "https://github.com/owner_user/repo-user-cascade",
            "default_branch": "main",
        },
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=owner.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    # Deleting member_user should remove their membership
    member_id = member.id
    db_session.delete(member_user)
    db_session.commit()

    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.id == member_id).first() is None
    # Team still exists
    assert db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first() is not None


def test_revival_team_schemas(db_session, test_user, test_repo):
    """Verify Pydantic schemas serialize safe fields and do not expose sensitive tokens."""
    team = RevivalTeam(
        repository_id=test_repo.id,
        owner_id=test_user.id,
    )
    db_session.add(team)
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=33301,
        username="schema_user",
        name="Schema User",
        avatar_url="https://avatar.url/s",
        access_token="super_secret_token_never_expose",
    )
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()
    db_session.refresh(team)
    db_session.refresh(member)

    # Validate member schema
    member_data = RevivalTeamMemberResponse.model_validate(member).model_dump()
    assert member_data["id"] == member.id
    assert member_data["team_id"] == team.id
    assert member_data["user_id"] == dev.id
    assert member_data["user"]["username"] == "schema_user"
    assert "access_token" not in member_data["user"]
    assert "access_token" not in member_data

    # Validate team schema
    team_data = RevivalTeamResponse.model_validate(team).model_dump()
    assert team_data["id"] == team.id
    assert team_data["repository_id"] == test_repo.id
    assert team_data["owner_id"] == test_user.id
    assert team_data["owner"]["username"] == test_user.username
    assert "access_token" not in team_data["owner"]
    assert "access_token" not in team_data
    assert len(team_data["members"]) == 1
    assert team_data["members"][0]["user"]["username"] == "schema_user"


def test_first_approval_creates_team_and_member(client, db_session, test_user, auth_context):
    """Verify owner approval creates RevivalTeam with correct owner and adds requester as member."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1001,
            "name": "approval-repo-1",
            "full_name": "testuser/approval-repo-1",
            "html_url": "https://github.com/testuser/approval-repo-1",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20001,
        username="dev_first_approval",
        name="Dev First Approval",
        avatar_url="https://avatar.url/devb",
        access_token="tok_b",
    )
    db_session.commit()

    # Developer B submits revival request
    auth_context.user = dev_b
    res_b = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "I want to revive this project"},
    )
    assert res_b.status_code == 201
    request_id = res_b.json()["id"]

    # Owner approves request
    auth_context.user = test_user
    res_approve = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res_approve.status_code == 200
    data = res_approve.json()
    assert data["status"] == "approved"
    assert data["requester"]["username"] == "dev_first_approval"

    # Verify RevivalTeam is automatically created
    team = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first()
    assert team is not None
    assert team.repository_id == repo.id
    assert team.owner_id == test_user.id

    # Verify requester is added as RevivalTeamMember
    assert len(team.members) == 1
    member = team.members[0]
    assert member.user_id == dev_b.id
    assert member.team_id == team.id
    assert member.user.username == "dev_first_approval"


def test_approval_reuses_existing_team_for_second_member(client, db_session, test_user, auth_context):
    """Verify approving another request reuses existing RevivalTeam and repository has exactly one team."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1002,
            "name": "approval-repo-2",
            "full_name": "testuser/approval-repo-2",
            "html_url": "https://github.com/testuser/approval-repo-2",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20002,
        username="dev_member_1",
        name="Dev 1",
        avatar_url=None,
        access_token="tok_1",
    )
    dev_c = create_user(
        db=db_session,
        github_id=20003,
        username="dev_member_2",
        name="Dev 2",
        avatar_url=None,
        access_token="tok_2",
    )
    db_session.commit()

    auth_context.user = dev_b
    res_b = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "From dev b"})
    req_b_id = res_b.json()["id"]

    auth_context.user = dev_c
    res_c = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "From dev c"})
    req_c_id = res_c.json()["id"]

    # Owner approves dev_b
    auth_context.user = test_user
    res_app_b = client.post(f"/repositories/{repo.id}/revival-requests/{req_b_id}/approve")
    assert res_app_b.status_code == 200

    team_first = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first()
    assert team_first is not None
    team_id = team_first.id

    # Owner approves dev_c
    res_app_c = client.post(f"/repositories/{repo.id}/revival-requests/{req_c_id}/approve")
    assert res_app_c.status_code == 200

    # Verify exactly one team exists for repo, and it is the same team
    teams = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).all()
    assert len(teams) == 1
    assert teams[0].id == team_id

    # Verify both members exist
    db_session.refresh(team_first)
    assert len(team_first.members) == 2
    member_user_ids = {m.user_id for m in team_first.members}
    assert member_user_ids == {dev_b.id, dev_c.id}


def test_duplicate_membership_protection(client, db_session, test_user, auth_context):
    """Verify approval does not create duplicate membership if user is already a member."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1003,
            "name": "approval-repo-3",
            "full_name": "testuser/approval-repo-3",
            "html_url": "https://github.com/testuser/approval-repo-3",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20004,
        username="dev_dupe_check",
        name="Dev Dupe",
        avatar_url=None,
        access_token="tok_d",
    )
    db_session.commit()

    # Pre-create team and member
    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    existing_mem = RevivalTeamMember(team_id=team.id, user_id=dev_b.id)
    db_session.add(existing_mem)
    db_session.commit()

    # dev_b submits request
    auth_context.user = dev_b
    res_b = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Hello"})
    req_id = res_b.json()["id"]

    # Owner approves
    auth_context.user = test_user
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    # Ensure still only 1 membership
    members = db_session.query(RevivalTeamMember).filter(
        RevivalTeamMember.team_id == team.id,
        RevivalTeamMember.user_id == dev_b.id,
    ).all()
    assert len(members) == 1


def test_request_state_protections(client, db_session, test_user, auth_context):
    """Verify already-decided requests cannot be approved or rejected again."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1004,
            "name": "approval-repo-4",
            "full_name": "testuser/approval-repo-4",
            "html_url": "https://github.com/testuser/approval-repo-4",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20005,
        username="dev_states_b",
        name="Dev States B",
        avatar_url=None,
        access_token="tok_b",
    )
    dev_c = create_user(
        db=db_session,
        github_id=20006,
        username="dev_states_c",
        name="Dev States C",
        avatar_url=None,
        access_token="tok_c",
    )
    db_session.commit()

    # dev_b request -> approved
    auth_context.user = dev_b
    req_b_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "B"}).json()["id"]

    auth_context.user = test_user
    res_app = client.post(f"/repositories/{repo.id}/revival-requests/{req_b_id}/approve")
    assert res_app.status_code == 200

    # Cannot approve already-approved request
    res_re_approve = client.post(f"/repositories/{repo.id}/revival-requests/{req_b_id}/approve")
    assert res_re_approve.status_code == 409

    # Cannot reject already-approved request
    res_rej_approved = client.post(f"/repositories/{repo.id}/revival-requests/{req_b_id}/reject")
    assert res_rej_approved.status_code == 409

    # dev_c request -> rejected
    auth_context.user = dev_c
    req_c_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "C"}).json()["id"]

    auth_context.user = test_user
    res_rej = client.post(f"/repositories/{repo.id}/revival-requests/{req_c_id}/reject")
    assert res_rej.status_code == 200

    # Cannot approve rejected request
    res_app_rejected = client.post(f"/repositories/{repo.id}/revival-requests/{req_c_id}/approve")
    assert res_app_rejected.status_code == 409

    # Cannot reject already-rejected request
    res_re_reject = client.post(f"/repositories/{repo.id}/revival-requests/{req_c_id}/reject")
    assert res_re_reject.status_code == 409


def test_rejection_does_not_create_team_or_member(client, db_session, test_user, auth_context):
    """Verify rejection does not create RevivalTeam or RevivalTeamMember."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1005,
            "name": "approval-repo-5",
            "full_name": "testuser/approval-repo-5",
            "html_url": "https://github.com/testuser/approval-repo-5",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20007,
        username="dev_reject_no_team",
        name="Dev Reject",
        avatar_url=None,
        access_token="tok_rej",
    )
    db_session.commit()

    auth_context.user = dev_b
    req_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Reject me"}).json()["id"]

    auth_context.user = test_user
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/reject")
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    # Assert no team created
    assert db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first() is None
    # Assert no member created
    assert db_session.query(RevivalTeamMember).count() == 0


def test_approval_authorization_and_privacy(client, db_session, test_user, auth_context):
    """Verify authorization checks for approval and rejection endpoints."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1006,
            "name": "approval-repo-6",
            "full_name": "testuser/approval-repo-6",
            "html_url": "https://github.com/testuser/approval-repo-6",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20008,
        username="dev_auth_b",
        name="Dev Auth B",
        avatar_url=None,
        access_token="tok_auth_b",
    )
    dev_c = create_user(
        db=db_session,
        github_id=20009,
        username="dev_auth_c",
        name="Dev Auth C",
        avatar_url=None,
        access_token="tok_auth_c",
    )
    db_session.commit()

    auth_context.user = dev_b
    req_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Auth test"}).json()["id"]

    # 1. Unauthenticated user cannot approve (401)
    auth_context.user = None
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")
    assert res.status_code == 401

    # 2. Non-owner (dev_c) cannot approve (404 for privacy)
    auth_context.user = dev_c
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")
    assert res.status_code == 404

    # 3. Requester (dev_b) cannot approve their own request (404)
    auth_context.user = dev_b
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")
    assert res.status_code == 404

    # 4. Non-owner cannot reject (404)
    auth_context.user = dev_c
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/reject")
    assert res.status_code == 404

    # 5. Wrong repository/request combination returns 404
    auth_context.user = test_user
    res = client.post(f"/repositories/99999/revival-requests/{req_id}/approve")
    assert res.status_code == 404


def test_approval_on_unpublished_repository(client, db_session, test_user, auth_context):
    """Verify owner can approve request on an unpublished repository and team is created."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 1007,
            "name": "approval-repo-7",
            "full_name": "testuser/approval-repo-7",
            "html_url": "https://github.com/testuser/approval-repo-7",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=20010,
        username="dev_unpub",
        name="Dev Unpub",
        avatar_url=None,
        access_token="tok_unpub",
    )
    db_session.commit()

    auth_context.user = dev_b
    req_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Unpub test"}).json()["id"]

    # Owner unpublishes repository
    repo.published = False
    db_session.commit()

    # Owner approves request
    auth_context.user = test_user
    res = client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    # Team and member exist
    team = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first()
    assert team is not None
    assert team.owner_id == test_user.id
    assert len(team.members) == 1
    assert team.members[0].user_id == dev_b.id
