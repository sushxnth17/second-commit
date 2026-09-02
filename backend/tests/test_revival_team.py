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


def test_get_revival_team_owner_access(client, db_session, test_user, auth_context):
    """Verify owner can retrieve Revival Team and team contents are correct."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2001,
            "name": "get-team-repo-1",
            "full_name": "testuser/get-team-repo-1",
            "html_url": "https://github.com/testuser/get-team-repo-1",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_b = create_user(
        db=db_session,
        github_id=30001,
        username="dev_member_api",
        name="Dev Member API",
        avatar_url="https://avatar.url/api",
        access_token="tok_api_secret",
    )
    db_session.commit()

    auth_context.user = dev_b
    req_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Revive"}).json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")

    # Retrieve team as owner
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    data = res.json()

    # Verify team metadata
    assert data["repository_id"] == repo.id
    assert data["owner_id"] == test_user.id
    assert data["owner"]["username"] == test_user.username
    assert "access_token" not in data["owner"]
    assert "access_token" not in data

    # Verify members
    assert len(data["members"]) == 1
    m = data["members"][0]
    assert m["user_id"] == dev_b.id
    assert m["username"] == "dev_member_api"
    assert m["name"] == "Dev Member API"
    assert m["avatar_url"] == "https://avatar.url/api"
    assert "access_token" not in m
    if m.get("user"):
        assert "access_token" not in m["user"]

    # Owner is not duplicated as a member
    member_user_ids = [mem["user_id"] for mem in data["members"]]
    assert test_user.id not in member_user_ids


def test_get_revival_team_published_visitor_access(client, db_session, test_user, auth_context):
    """Verify any authenticated visitor can retrieve team for a published repository."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2002,
            "name": "get-team-repo-2",
            "full_name": "testuser/get-team-repo-2",
            "html_url": "https://github.com/testuser/get-team-repo-2",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    visitor = create_user(
        db=db_session,
        github_id=30002,
        username="visitor_user",
        name="Visitor",
        avatar_url=None,
        access_token="tok_vis",
    )
    dev_b = create_user(
        db=db_session,
        github_id=30003,
        username="dev_team_b",
        name="Dev Team B",
        avatar_url=None,
        access_token="tok_b",
    )
    db_session.commit()

    auth_context.user = dev_b
    req_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Join"}).json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")

    # Visitor retrieves team
    auth_context.user = visitor
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    assert res.json()["repository_id"] == repo.id
    assert len(res.json()["members"]) == 1


def test_get_revival_team_unauthenticated(client, db_session, test_user, auth_context):
    """Verify unauthenticated user receives 401."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2003,
            "name": "get-team-repo-3",
            "full_name": "testuser/get-team-repo-3",
            "html_url": "https://github.com/testuser/get-team-repo-3",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    auth_context.user = None
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 401


def test_get_revival_team_unpublished_non_owner_forbidden(client, db_session, test_user, auth_context):
    """Verify non-owner non-member receives 404 when repository is unpublished."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2004,
            "name": "get-team-repo-4",
            "full_name": "testuser/get-team-repo-4",
            "html_url": "https://github.com/testuser/get-team-repo-4",
            "default_branch": "main",
        },
    )
    repo.published = False
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    other_user = create_user(
        db=db_session,
        github_id=30004,
        username="random_user",
        name="Random",
        avatar_url=None,
        access_token="tok_rnd",
    )
    db_session.commit()

    auth_context.user = other_user
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_get_revival_team_unpublished_owner_access(client, db_session, test_user, auth_context):
    """Verify owner can view team even if repository is unpublished."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2005,
            "name": "get-team-repo-5",
            "full_name": "testuser/get-team-repo-5",
            "html_url": "https://github.com/testuser/get-team-repo-5",
            "default_branch": "main",
        },
    )
    repo.published = False
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    assert res.json()["repository_id"] == repo.id


def test_get_revival_team_unpublished_member_access(client, db_session, test_user, auth_context):
    """Verify an approved team member can view team even if repository is unpublished."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2006,
            "name": "get-team-repo-6",
            "full_name": "testuser/get-team-repo-6",
            "html_url": "https://github.com/testuser/get-team-repo-6",
            "default_branch": "main",
        },
    )
    repo.published = False
    db_session.commit()

    dev_member = create_user(
        db=db_session,
        github_id=30005,
        username="member_of_unpub",
        name="Member Unpub",
        avatar_url=None,
        access_token="tok_unpub_mem",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev_member.id)
    db_session.add(member)
    db_session.commit()

    # Member accesses team on unpublished repository
    auth_context.user = dev_member
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    assert res.json()["repository_id"] == repo.id
    assert len(res.json()["members"]) == 1


def test_get_revival_team_no_team_exists(client, db_session, test_user, auth_context):
    """Verify 404 with detail 'Revival team not found' when repository has no team."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2007,
            "name": "get-team-repo-7",
            "full_name": "testuser/get-team-repo-7",
            "html_url": "https://github.com/testuser/get-team-repo-7",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 404
    assert res.json()["detail"] == "Revival team not found"


def test_get_revival_team_excludes_pending_and_rejected_requests(client, db_session, test_user, auth_context):
    """Verify only approved members appear; pending and rejected requests are excluded."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2008,
            "name": "get-team-repo-8",
            "full_name": "testuser/get-team-repo-8",
            "html_url": "https://github.com/testuser/get-team-repo-8",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_approved = create_user(db=db_session, github_id=30006, username="dev_appr", name="Appr", avatar_url=None, access_token="tok_a")
    dev_pending = create_user(db=db_session, github_id=30007, username="dev_pend", name="Pend", avatar_url=None, access_token="tok_p")
    dev_rejected = create_user(db=db_session, github_id=30008, username="dev_rejd", name="Rejd", avatar_url=None, access_token="tok_r")
    db_session.commit()

    auth_context.user = dev_approved
    app_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Appr"}).json()["id"]

    auth_context.user = dev_pending
    client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Pend"})

    auth_context.user = dev_rejected
    rej_id = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Rej"}).json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{app_id}/approve")
    client.post(f"/repositories/{repo.id}/revival-requests/{rej_id}/reject")

    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    data = res.json()
    assert len(data["members"]) == 1
    assert data["members"][0]["user_id"] == dev_approved.id

    member_usernames = {m["username"] for m in data["members"]}
    assert "dev_appr" in member_usernames
    assert "dev_pend" not in member_usernames
    assert "dev_rejd" not in member_usernames


def test_get_revival_team_deterministic_ordering(client, db_session, test_user, auth_context):
    """Verify members are returned in deterministic order: joined_at ASC."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 2009,
            "name": "get-team-repo-9",
            "full_name": "testuser/get-team-repo-9",
            "html_url": "https://github.com/testuser/get-team-repo-9",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_1 = create_user(db=db_session, github_id=30011, username="order_dev_1", name="Dev 1", avatar_url=None, access_token="tok_1")
    dev_2 = create_user(db=db_session, github_id=30012, username="order_dev_2", name="Dev 2", avatar_url=None, access_token="tok_2")
    dev_3 = create_user(db=db_session, github_id=30013, username="order_dev_3", name="Dev 3", avatar_url=None, access_token="tok_3")
    db_session.commit()

    auth_context.user = dev_1
    req_1 = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "1"}).json()["id"]
    auth_context.user = dev_2
    req_2 = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "2"}).json()["id"]
    auth_context.user = dev_3
    req_3 = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "3"}).json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_1}/approve")
    client.post(f"/repositories/{repo.id}/revival-requests/{req_2}/approve")
    client.post(f"/repositories/{repo.id}/revival-requests/{req_3}/approve")

    res = client.get(f"/repositories/{repo.id}/revival-team")
    assert res.status_code == 200
    members = res.json()["members"]
    assert len(members) == 3
    assert members[0]["user_id"] == dev_1.id
    assert members[1]["user_id"] == dev_2.id
    assert members[2]["user_id"] == dev_3.id


def test_owner_can_remove_existing_member(client, db_session, test_user, auth_context):
    """1. Owner can remove an existing member and receives 204 No Content."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4001,
            "name": "team-remove-1",
            "full_name": "testuser/team-remove-1",
            "html_url": "https://github.com/testuser/team-remove-1",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40001,
        username="dev_remove_1",
        name="Dev Remove 1",
        avatar_url=None,
        access_token="tok_rem_1",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res.status_code == 204
    assert res.content == b""

    # Verify membership row is deleted in DB
    remaining_member = (
        db_session.query(RevivalTeamMember)
        .filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev.id)
        .first()
    )
    assert remaining_member is None


def test_removed_member_no_longer_appears_in_get_team(client, db_session, test_user, auth_context):
    """2. Removed member no longer appears in GET /revival-team."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4002,
            "name": "team-remove-2",
            "full_name": "testuser/team-remove-2",
            "html_url": "https://github.com/testuser/team-remove-2",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40002,
        username="dev_remove_2",
        name="Dev Remove 2",
        avatar_url=None,
        access_token="tok_rem_2",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    # Pre-check: member is in GET
    auth_context.user = test_user
    res_before = client.get(f"/repositories/{repo.id}/revival-team")
    assert res_before.status_code == 200
    assert len(res_before.json()["members"]) == 1

    # Remove member
    res_del = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res_del.status_code == 204

    # Post-check: member is no longer in GET
    res_after = client.get(f"/repositories/{repo.id}/revival-team")
    assert res_after.status_code == 200
    assert len(res_after.json()["members"]) == 0


def test_non_owner_cannot_remove_member(client, db_session, test_user, auth_context):
    """3. Non-owner cannot remove a member and receives 404 for privacy."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4003,
            "name": "team-remove-3",
            "full_name": "testuser/team-remove-3",
            "html_url": "https://github.com/testuser/team-remove-3",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_member = create_user(
        db=db_session,
        github_id=40003,
        username="dev_member_3",
        name="Dev Member 3",
        avatar_url=None,
        access_token="tok_rem_3",
    )
    dev_other = create_user(
        db=db_session,
        github_id=40004,
        username="dev_other_3",
        name="Dev Other 3",
        avatar_url=None,
        access_token="tok_rem_other_3",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev_member.id)
    db_session.add(member)
    db_session.commit()

    # dev_other attempts to remove dev_member
    auth_context.user = dev_other
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_member.id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"

    # Member still in DB
    assert (
        db_session.query(RevivalTeamMember)
        .filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_member.id)
        .first()
        is not None
    )


def test_unauthenticated_cannot_remove_member(client, db_session, test_user, auth_context):
    """4. Unauthenticated user cannot remove a member and receives 401."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4004,
            "name": "team-remove-4",
            "full_name": "testuser/team-remove-4",
            "html_url": "https://github.com/testuser/team-remove-4",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40005,
        username="dev_unauth_4",
        name="Dev Unauth 4",
        avatar_url=None,
        access_token="tok_rem_4",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = None
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res.status_code == 401


def test_removing_nonexistent_member_returns_404(client, db_session, test_user, auth_context):
    """5. Removing a nonexistent member returns 404."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4005,
            "name": "team-remove-5",
            "full_name": "testuser/team-remove-5",
            "html_url": "https://github.com/testuser/team-remove-5",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/99999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Team member not found"


def test_owner_cannot_remove_themselves(client, db_session, test_user, auth_context):
    """6. Owner cannot remove themselves through the member removal endpoint."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4006,
            "name": "team-remove-6",
            "full_name": "testuser/team-remove-6",
            "html_url": "https://github.com/testuser/team-remove-6",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{test_user.id}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Team owner cannot be removed from the revival team."


def test_remove_member_does_not_delete_user(client, db_session, test_user, auth_context):
    """7. Removing a member does not delete the User account."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4007,
            "name": "team-remove-7",
            "full_name": "testuser/team-remove-7",
            "html_url": "https://github.com/testuser/team-remove-7",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40007,
        username="dev_keep_user",
        name="Dev Keep User",
        avatar_url=None,
        access_token="tok_keep_7",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res.status_code == 204

    # Confirm user still exists
    user_in_db = db_session.query(User).filter(User.id == dev.id).first()
    assert user_in_db is not None
    assert user_in_db.username == "dev_keep_user"


def test_remove_member_does_not_delete_team(client, db_session, test_user, auth_context):
    """8. Removing a member does not delete the RevivalTeam."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4008,
            "name": "team-remove-8",
            "full_name": "testuser/team-remove-8",
            "html_url": "https://github.com/testuser/team-remove-8",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40008,
        username="dev_keep_team",
        name="Dev Keep Team",
        avatar_url=None,
        access_token="tok_keep_8",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res.status_code == 204

    # Confirm team still exists
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.owner_id == test_user.id


def test_remove_member_does_not_alter_revival_request(client, db_session, test_user, auth_context):
    """9. Removing a member does not alter or delete the RevivalRequest."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4009,
            "name": "team-remove-9",
            "full_name": "testuser/team-remove-9",
            "html_url": "https://github.com/testuser/team-remove-9",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40009,
        username="dev_keep_req",
        name="Dev Keep Req",
        avatar_url=None,
        access_token="tok_keep_9",
    )
    db_session.commit()

    # Dev submits request and owner approves
    auth_context.user = dev
    req_res = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Join"})
    req_id = req_res.json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")

    # Owner removes member
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res.status_code == 204

    # Check request status remains approved
    req_in_db = db_session.query(RevivalRequest).filter(RevivalRequest.id == req_id).first()
    assert req_in_db is not None
    assert req_in_db.status == "approved"
    assert req_in_db.requester_id == dev.id


def test_team_member_can_leave(client, db_session, test_user, auth_context):
    """10. Team member can leave using DELETE .../members/me."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4010,
            "name": "team-leave-10",
            "full_name": "testuser/team-leave-10",
            "html_url": "https://github.com/testuser/team-leave-10",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40010,
        username="dev_leave_10",
        name="Dev Leave 10",
        avatar_url=None,
        access_token="tok_leave_10",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = dev
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 204
    assert res.content == b""

    # Member is gone from DB
    remaining_member = (
        db_session.query(RevivalTeamMember)
        .filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev.id)
        .first()
    )
    assert remaining_member is None


def test_leaving_removes_only_that_membership(client, db_session, test_user, auth_context):
    """11. Leaving removes only that caller's membership, other members remain."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4011,
            "name": "team-leave-11",
            "full_name": "testuser/team-leave-11",
            "html_url": "https://github.com/testuser/team-leave-11",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_1 = create_user(db=db_session, github_id=40011, username="leave_dev_1", name="Dev 1", avatar_url=None, access_token="tok_11_1")
    dev_2 = create_user(db=db_session, github_id=40012, username="leave_dev_2", name="Dev 2", avatar_url=None, access_token="tok_11_2")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    m1 = RevivalTeamMember(team_id=team.id, user_id=dev_1.id)
    m2 = RevivalTeamMember(team_id=team.id, user_id=dev_2.id)
    db_session.add_all([m1, m2])
    db_session.commit()

    # dev_1 leaves
    auth_context.user = dev_1
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 204

    # dev_1 is deleted, dev_2 still exists
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_1.id).first() is None
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_2.id).first() is not None

    # GET /revival-team shows dev_2
    auth_context.user = test_user
    res_get = client.get(f"/repositories/{repo.id}/revival-team")
    assert res_get.status_code == 200
    members = res_get.json()["members"]
    assert len(members) == 1
    assert members[0]["user_id"] == dev_2.id


def test_non_member_cannot_leave(client, db_session, test_user, auth_context):
    """12. User who is not a member cannot leave and receives 404."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4012,
            "name": "team-leave-12",
            "full_name": "testuser/team-leave-12",
            "html_url": "https://github.com/testuser/team-leave-12",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40013,
        username="dev_non_member",
        name="Dev Non Member",
        avatar_url=None,
        access_token="tok_leave_12",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = dev
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 404
    assert res.json()["detail"] == "Team member not found"


def test_unauthenticated_cannot_leave(client, db_session, test_user, auth_context):
    """13. Unauthenticated user cannot leave and receives 401."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4013,
            "name": "team-leave-13",
            "full_name": "testuser/team-leave-13",
            "html_url": "https://github.com/testuser/team-leave-13",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = None
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 401


def test_team_owner_cannot_leave(client, db_session, test_user, auth_context):
    """14. Team owner cannot leave through the leave endpoint."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4014,
            "name": "team-leave-14",
            "full_name": "testuser/team-leave-14",
            "html_url": "https://github.com/testuser/team-leave-14",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 400
    assert res.json()["detail"] == "Team owner cannot leave the revival team."

    # Team remains intact
    assert db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first() is not None


def test_leaving_does_not_delete_user(client, db_session, test_user, auth_context):
    """15. Leaving does not delete the User account."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4015,
            "name": "team-leave-15",
            "full_name": "testuser/team-leave-15",
            "html_url": "https://github.com/testuser/team-leave-15",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40015,
        username="dev_leave_keep_user",
        name="Dev Leave Keep User",
        avatar_url=None,
        access_token="tok_leave_15",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = dev
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 204

    # User still exists
    user_in_db = db_session.query(User).filter(User.id == dev.id).first()
    assert user_in_db is not None
    assert user_in_db.username == "dev_leave_keep_user"


def test_leaving_does_not_delete_team(client, db_session, test_user, auth_context):
    """16. Leaving does not delete the RevivalTeam."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4016,
            "name": "team-leave-16",
            "full_name": "testuser/team-leave-16",
            "html_url": "https://github.com/testuser/team-leave-16",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40016,
        username="dev_leave_keep_team",
        name="Dev Leave Keep Team",
        avatar_url=None,
        access_token="tok_leave_16",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = dev
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 204

    # Team still exists
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.owner_id == test_user.id


def test_leaving_does_not_alter_revival_request(client, db_session, test_user, auth_context):
    """17. Leaving does not alter or delete the RevivalRequest."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4017,
            "name": "team-leave-17",
            "full_name": "testuser/team-leave-17",
            "html_url": "https://github.com/testuser/team-leave-17",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(
        db=db_session,
        github_id=40017,
        username="dev_leave_keep_req",
        name="Dev Leave Keep Req",
        avatar_url=None,
        access_token="tok_leave_17",
    )
    db_session.commit()

    auth_context.user = dev
    req_res = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "Revive"})
    req_id = req_res.json()["id"]

    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_id}/approve")

    # Member leaves
    auth_context.user = dev
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 204

    # Request remains approved
    req_in_db = db_session.query(RevivalRequest).filter(RevivalRequest.id == req_id).first()
    assert req_in_db is not None
    assert req_in_db.status == "approved"
    assert req_in_db.requester_id == dev.id


def test_unpublished_repository_access_protected_on_remove_and_leave(client, db_session, test_user, auth_context):
    """18. Unpublished repository access remains protected against unauthorized inspection."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4018,
            "name": "team-unpub-18",
            "full_name": "testuser/team-unpub-18",
            "html_url": "https://github.com/testuser/team-unpub-18",
            "default_branch": "main",
        },
    )
    repo.published = False
    db_session.commit()

    dev_member = create_user(db=db_session, github_id=40018, username="unpub_member", name="Unpub Member", avatar_url=None, access_token="tok_unpub_18")
    dev_outsider = create_user(db=db_session, github_id=40019, username="unpub_outsider", name="Unpub Outsider", avatar_url=None, access_token="tok_unpub_19")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev_member.id)
    db_session.add(member)
    db_session.commit()

    # Outsider calling DELETE /members/{user_id} gets 404 "Repository not found"
    auth_context.user = dev_outsider
    res_del_other = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_member.id}")
    assert res_del_other.status_code == 404
    assert res_del_other.json()["detail"] == "Repository not found"

    # Outsider calling DELETE /members/me gets 404 "Repository not found"
    res_leave_outsider = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_leave_outsider.status_code == 404
    assert res_leave_outsider.json()["detail"] == "Repository not found"

    # Legitimate member on unpublished repo can leave
    auth_context.user = dev_member
    res_leave_member = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_leave_member.status_code == 204

    # Re-add member for owner removal test
    member2 = RevivalTeamMember(team_id=team.id, user_id=dev_member.id)
    db_session.add(member2)
    db_session.commit()

    # Owner on unpublished repo can remove member
    auth_context.user = test_user
    res_owner_del = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_member.id}")
    assert res_owner_del.status_code == 204


def test_user_cannot_use_members_me_to_remove_another_user(client, db_session, test_user, auth_context):
    """19. A user cannot pass parameters or body to /members/me to remove another user."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4019,
            "name": "team-me-tamper-19",
            "full_name": "testuser/team-me-tamper-19",
            "html_url": "https://github.com/testuser/team-me-tamper-19",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_1 = create_user(db=db_session, github_id=40020, username="dev_me_1", name="Dev 1", avatar_url=None, access_token="tok_me_1")
    dev_2 = create_user(db=db_session, github_id=40021, username="dev_me_2", name="Dev 2", avatar_url=None, access_token="tok_me_2")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    m1 = RevivalTeamMember(team_id=team.id, user_id=dev_1.id)
    m2 = RevivalTeamMember(team_id=team.id, user_id=dev_2.id)
    db_session.add_all([m1, m2])
    db_session.commit()

    # dev_1 calls /members/me attempting to pass dev_2's user_id via query params
    auth_context.user = dev_1
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me?user_id={dev_2.id}")
    assert res.status_code == 204

    # dev_1 was removed, dev_2 was NOT removed
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_1.id).first() is None
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_2.id).first() is not None


def test_membership_operations_respect_authoritative_team_owner_id(client, db_session, test_user, auth_context):
    """20. Membership operations strictly respect authoritative RevivalTeam.owner_id over Repository.owner_id."""
    # Create repo owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 4020,
            "name": "team-authoritative-20",
            "full_name": "testuser/team-authoritative-20",
            "html_url": "https://github.com/testuser/team-authoritative-20",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    # Team owner is team_leader (different from repo owner test_user)
    team_leader = create_user(db=db_session, github_id=40022, username="team_leader_20", name="Leader", avatar_url=None, access_token="tok_ldr_20")
    dev_member = create_user(db=db_session, github_id=40023, username="dev_member_20", name="Member", avatar_url=None, access_token="tok_mem_20")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=team_leader.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev_member.id)
    db_session.add(member)
    db_session.commit()

    # 1. Repository owner (test_user) attempts to remove member -> forbidden (404 for privacy) because not team_leader
    auth_context.user = test_user
    res_repo_owner = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_member.id}")
    assert res_repo_owner.status_code == 404
    assert res_repo_owner.json()["detail"] == "Repository not found"

    # 2. Team owner (team_leader) attempts to leave via /members/me -> rejected with 400
    auth_context.user = team_leader
    res_leader_leave = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_leader_leave.status_code == 400
    assert res_leader_leave.json()["detail"] == "Team owner cannot leave the revival team."

    # 3. Team owner (team_leader) removes member -> succeeds with 204
    res_leader_remove = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_member.id}")
    assert res_leader_remove.status_code == 204

    # Member is removed
    assert db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id, RevivalTeamMember.user_id == dev_member.id).first() is None


# ==============================================================================
# LIFECYCLE & STALE STATE INTEGRATION TESTS (Commit 3)
# ==============================================================================


def test_owner_remove_lifecycle_complete(client, db_session, test_user, auth_context):
    """Lifecycle test: Approved revival request -> team member -> owner removes -> 204 -> DB consistency."""
    # 1. Create repository and approved revival request
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5001,
            "name": "lifecycle-owner-remove",
            "full_name": "testuser/lifecycle-owner-remove",
            "html_url": "https://github.com/testuser/lifecycle-owner-remove",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    requester = create_user(
        db=db_session,
        github_id=50001,
        username="requester_remove",
        name="Requester Remove",
        avatar_url="https://avatar.url/req_rem",
        access_token="tok_req_rem",
    )
    db_session.commit()

    # Submit revival request
    auth_context.user = requester
    req_res = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "I want to help revive this project!"},
    )
    assert req_res.status_code == 201
    request_id = req_res.json()["id"]

    # Owner approves request
    auth_context.user = test_user
    appr_res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert appr_res.status_code == 200

    # 2. Verify team exists
    team = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first()
    assert team is not None
    assert team.owner_id == test_user.id

    # 3. Verify requester is a member
    member = db_session.query(RevivalTeamMember).filter(
        RevivalTeamMember.team_id == team.id,
        RevivalTeamMember.user_id == requester.id,
    ).first()
    assert member is not None

    team_get = client.get(f"/repositories/{repo.id}/revival-team")
    assert team_get.status_code == 200
    assert any(m["user_id"] == requester.id for m in team_get.json()["members"])

    # 4. Owner removes requester
    del_res = client.delete(f"/repositories/{repo.id}/revival-team/members/{requester.id}")

    # 5. Verify DELETE returns 204
    assert del_res.status_code == 204

    # 6. GET team no longer contains requester
    team_get_after = client.get(f"/repositories/{repo.id}/revival-team")
    assert team_get_after.status_code == 200
    assert not any(m["user_id"] == requester.id for m in team_get_after.json()["members"])

    # 7. User still exists
    user_in_db = db_session.query(User).filter(User.id == requester.id).first()
    assert user_in_db is not None
    assert user_in_db.username == "requester_remove"

    # 8. RevivalTeam still exists
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.repository_id == repo.id
    assert team_in_db.owner_id == test_user.id

    # 9. RevivalRequest still exists and remains approved
    rev_req_in_db = db_session.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    assert rev_req_in_db is not None
    assert rev_req_in_db.status == "approved"


def test_member_leave_lifecycle_complete(client, db_session, test_user, auth_context):
    """Lifecycle test: Approved revival request -> team member -> member leaves -> 204 -> DB consistency."""
    # 10. Create repository and approved revival request
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5002,
            "name": "lifecycle-member-leave",
            "full_name": "testuser/lifecycle-member-leave",
            "html_url": "https://github.com/testuser/lifecycle-member-leave",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    requester = create_user(
        db=db_session,
        github_id=50002,
        username="requester_leave",
        name="Requester Leave",
        avatar_url="https://avatar.url/req_leave",
        access_token="tok_req_leave",
    )
    db_session.commit()

    # Submit revival request
    auth_context.user = requester
    req_res = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "I would love to join!"},
    )
    assert req_res.status_code == 201
    request_id = req_res.json()["id"]

    # Owner approves
    auth_context.user = test_user
    appr_res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert appr_res.status_code == 200

    # 11. Verify requester is a member
    team = db_session.query(RevivalTeam).filter(RevivalTeam.repository_id == repo.id).first()
    assert team is not None
    assert db_session.query(RevivalTeamMember).filter(
        RevivalTeamMember.team_id == team.id,
        RevivalTeamMember.user_id == requester.id,
    ).first() is not None

    # 12. Requester leaves
    auth_context.user = requester
    leave_res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")

    # 13. Verify DELETE returns 204
    assert leave_res.status_code == 204

    # 14. Verify requester is no longer a member
    assert db_session.query(RevivalTeamMember).filter(
        RevivalTeamMember.team_id == team.id,
        RevivalTeamMember.user_id == requester.id,
    ).first() is None

    # 15. User still exists
    user_in_db = db_session.query(User).filter(User.id == requester.id).first()
    assert user_in_db is not None
    assert user_in_db.username == "requester_leave"

    # 16. RevivalTeam still exists
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None

    # 17. RevivalRequest remains approved
    rev_req_in_db = db_session.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    assert rev_req_in_db is not None
    assert rev_req_in_db.status == "approved"


def test_stale_remove_member_twice(client, db_session, test_user, auth_context):
    """18-20. Stale state: Removing the same member twice returns 204 on first, 404 on second."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5003,
            "name": "stale-remove-twice",
            "full_name": "testuser/stale-remove-twice",
            "html_url": "https://github.com/testuser/stale-remove-twice",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(db=db_session, github_id=50003, username="dev_stale_1", name="Dev Stale", avatar_url=None, access_token="tok_s1")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user

    # 18-19. First remove succeeds
    res_1 = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res_1.status_code == 204

    # 20. Second remove returns 404
    res_2 = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev.id}")
    assert res_2.status_code == 404
    assert res_2.json()["detail"] == "Team member not found"


def test_stale_member_leave_twice(client, db_session, test_user, auth_context):
    """21-23. Stale state: Member leaving twice returns 204 on first, 404 on second."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5004,
            "name": "stale-leave-twice",
            "full_name": "testuser/stale-leave-twice",
            "html_url": "https://github.com/testuser/stale-leave-twice",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev = create_user(db=db_session, github_id=50004, username="dev_stale_2", name="Dev Stale 2", avatar_url=None, access_token="tok_s2")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = dev

    # 21-22. First leave succeeds
    res_1 = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_1.status_code == 204

    # 23. Second leave returns 404
    res_2 = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_2.status_code == 404
    assert res_2.json()["detail"] == "Team member not found"


def test_stale_member_leave_twice_unpublished(client, db_session, test_user, auth_context):
    """Stale state on unpublished repo: First leave returns 204, second leave returns 404 'Repository not found'."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5005,
            "name": "stale-leave-unpublished",
            "full_name": "testuser/stale-leave-unpublished",
            "html_url": "https://github.com/testuser/stale-leave-unpublished",
            "default_branch": "main",
        },
    )
    repo.published = False
    db_session.commit()

    dev = create_user(db=db_session, github_id=50005, username="dev_stale_unpub", name="Dev Unpub", avatar_url=None, access_token="tok_unpub")
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member = RevivalTeamMember(team_id=team.id, user_id=dev.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = dev

    # First leave succeeds
    res_1 = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_1.status_code == 204

    # Second leave: user is no longer a member and repo is unpublished -> 404 Repository not found
    res_2 = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res_2.status_code == 404
    assert res_2.json()["detail"] == "Repository not found"


def test_multi_member_owner_removes_one_preserves_others(client, db_session, test_user, auth_context):
    """24-28. Multi-member: Owner removes one member while other members, owner, and team remain intact."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5006,
            "name": "multi-member-team",
            "full_name": "testuser/multi-member-team",
            "html_url": "https://github.com/testuser/multi-member-team",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    dev_1 = create_user(db=db_session, github_id=50006, username="multi_dev_1", name="Dev 1", avatar_url=None, access_token="tok_m1")
    dev_2 = create_user(db=db_session, github_id=50007, username="multi_dev_2", name="Dev 2", avatar_url=None, access_token="tok_m2")
    dev_3 = create_user(db=db_session, github_id=50008, username="multi_dev_3", name="Dev 3", avatar_url=None, access_token="tok_m3")
    db_session.commit()

    # 24. Create team with multiple members
    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    m1 = RevivalTeamMember(team_id=team.id, user_id=dev_1.id)
    m2 = RevivalTeamMember(team_id=team.id, user_id=dev_2.id)
    m3 = RevivalTeamMember(team_id=team.id, user_id=dev_3.id)
    db_session.add_all([m1, m2, m3])
    db_session.commit()

    # 25. Owner removes dev_2
    auth_context.user = test_user
    res_del = client.delete(f"/repositories/{repo.id}/revival-team/members/{dev_2.id}")
    assert res_del.status_code == 204

    # 26. Verify other members remain in DB and in API GET response
    remaining_members = db_session.query(RevivalTeamMember).filter(RevivalTeamMember.team_id == team.id).all()
    remaining_user_ids = {m.user_id for m in remaining_members}
    assert dev_1.id in remaining_user_ids
    assert dev_3.id in remaining_user_ids
    assert dev_2.id not in remaining_user_ids

    team_res = client.get(f"/repositories/{repo.id}/revival-team")
    assert team_res.status_code == 200
    api_member_ids = {m["user_id"] for m in team_res.json()["members"]}
    assert dev_1.id in api_member_ids
    assert dev_3.id in api_member_ids
    assert dev_2.id not in api_member_ids

    # 27. Verify owner remains
    assert team.owner_id == test_user.id
    assert team_res.json()["owner"]["id"] == test_user.id

    # 28. Verify team remains
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.repository_id == repo.id

    # dev_2 user account still exists
    assert db_session.query(User).filter(User.id == dev_2.id).first() is not None


def test_owner_integrity_self_removal_rejected(client, db_session, test_user, auth_context):
    """29-31. Owner integrity: Owner cannot remove themselves; team and owner state remain intact."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5007,
            "name": "owner-integrity-repo",
            "full_name": "testuser/owner-integrity-repo",
            "html_url": "https://github.com/testuser/owner-integrity-repo",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user

    # 29-30. Attempt owner self-removal -> fails with 400
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/{test_user.id}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Team owner cannot be removed from the revival team."

    # 31. Verify owner membership/team state remains unchanged
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.owner_id == test_user.id


def test_owner_integrity_leave_team_rejected(client, db_session, test_user, auth_context):
    """Owner integrity: Owner cannot leave team via /members/me; team and owner state remain intact."""
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 5008,
            "name": "owner-leave-integrity-repo",
            "full_name": "testuser/owner-leave-integrity-repo",
            "html_url": "https://github.com/testuser/owner-leave-integrity-repo",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    team = RevivalTeam(repository_id=repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user

    # Attempt leave via /members/me -> fails with 400
    res = client.delete(f"/repositories/{repo.id}/revival-team/members/me")
    assert res.status_code == 400
    assert res.json()["detail"] == "Team owner cannot leave the revival team."

    # Team and owner state remain intact
    team_in_db = db_session.query(RevivalTeam).filter(RevivalTeam.id == team.id).first()
    assert team_in_db is not None
    assert team_in_db.owner_id == test_user.id
