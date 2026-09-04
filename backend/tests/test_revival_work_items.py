import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.repository import Repository
from app.models.revival_request import RevivalRequest
from app.models.revival_team import RevivalTeam
from app.models.revival_team_member import RevivalTeamMember
from app.models.revival_work_item import RevivalWorkItem
from app.models.user import User
from app.services.repository_service import create_repository
from app.services.user_service import create_user


# ==============================================================================
# 1. MODEL / CREATION TESTS
# ==============================================================================

def test_1_work_item_can_be_created_for_existing_team(db_session, test_user, test_repo):
    """1. Work item can be created for an existing team."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(
        team_id=team.id,
        title="Fix dependency issues",
        description="Update outdated packages",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.id is not None
    assert item.team_id == team.id
    assert item.team.id == team.id
    assert item in team.work_items


def test_2_default_status_is_todo(db_session, test_user, test_repo):
    """2. Default status is 'todo'."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(
        team_id=team.id,
        title="Reproduce bug",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.status == "todo"


def test_3_title_and_description_are_persisted(db_session, test_user, test_repo):
    """3. Title and description are persisted accurately."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(
        team_id=team.id,
        title="Modernize authentication",
        description="Migrate OAuth flow to latest standard.",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    persisted = db_session.query(RevivalWorkItem).filter_by(id=item.id).first()
    assert persisted is not None
    assert persisted.title == "Modernize authentication"
    assert persisted.description == "Migrate OAuth flow to latest standard."
    assert persisted.created_at is not None
    assert persisted.updated_at is not None


def test_4_unassigned_work_item_is_allowed(db_session, test_user, test_repo):
    """4. Unassigned work item is allowed (assignee_id is nullable)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(
        team_id=team.id,
        title="Clean up legacy code",
        assignee_id=None,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.assignee_id is None
    assert item.assignee is None


# ==============================================================================
# 2. CREATE AUTHORIZATION TESTS
# ==============================================================================

def test_5_team_owner_can_create_work_item(client, db_session, test_user, test_repo, auth_context):
    """5. Team owner can create a work item."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    payload = {
        "title": "Fix dependency issues",
        "description": "Update outdated packages",
    }
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["title"] == "Fix dependency issues"
    assert data["description"] == "Update outdated packages"
    assert data["status"] == "todo"
    assert data["assignee"] is None

    # Check DB state
    db_item = db_session.query(RevivalWorkItem).filter_by(id=data["id"]).first()
    assert db_item is not None
    assert db_item.team_id == team.id


def test_6_team_member_cannot_create_work_item(client, db_session, test_user, test_repo, auth_context):
    """6. Team member cannot create a work item."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90001,
        username="team_member_1",
        name="Member One",
        avatar_url="https://avatar.url/1",
        access_token="tok_1",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = member_user
    payload = {"title": "Member attempted task", "description": "Should fail"}
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"

    # DB not mutated
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_7_unauthenticated_user_cannot_create(client, db_session, test_user, test_repo, auth_context):
    """7. Unauthenticated user cannot create a work item."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = None
    payload = {"title": "Unauthenticated task"}
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 401
    assert res.json()["detail"] == "Not authenticated"

    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_8_unauthorized_user_cannot_create(client, db_session, test_user, test_repo, auth_context):
    """8. Unauthorized user cannot create a work item."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=90002,
        username="outsider_user",
        name="Outsider",
        avatar_url="https://avatar.url/outsider",
        access_token="tok_outsider",
    )
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = outsider
    payload = {"title": "Outsider task"}
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"

    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_9_repository_owner_is_not_authorized_if_not_team_owner(client, db_session, test_user, test_repo, auth_context):
    """9. Repository owner is not automatically authorized if they are not the RevivalTeam.owner_id."""
    different_team_owner = create_user(
        db=db_session,
        github_id=90003,
        username="revival_lead",
        name="Revival Lead",
        avatar_url="https://avatar.url/lead",
        access_token="tok_lead",
    )
    db_session.commit()

    # test_repo.owner_id is test_user.id, but RevivalTeam.owner_id is different_team_owner.id
    team = RevivalTeam(repository_id=test_repo.id, owner_id=different_team_owner.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    # Repo owner attempts POST -> denied with 404
    auth_context.user = test_user
    payload = {"title": "Repo owner task"}
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"

    assert db_session.query(RevivalWorkItem).count() == initial_count

    # Team owner attempts POST -> succeeds
    auth_context.user = different_team_owner
    res_ok = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res_ok.status_code == 201


# ==============================================================================
# 3. ASSIGNEE TESTS
# ==============================================================================

def test_10_existing_team_member_can_be_assigned(client, db_session, test_user, test_repo, auth_context):
    """10. Existing team member can be assigned."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90004,
        username="member_assignee",
        name="Member Assignee",
        avatar_url="https://avatar.url/assignee",
        access_token="tok_assignee",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user
    payload = {
        "title": "Assigned task",
        "description": "Task for team member",
        "assignee_id": member_user.id,
    }
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["assignee"] is not None
    assert data["assignee"]["id"] == member_user.id
    assert data["assignee"]["username"] == "member_assignee"
    assert data["assignee"]["name"] == "Member Assignee"
    assert data["assignee"]["avatar_url"] == "https://avatar.url/assignee"

    # Verify DB
    db_item = db_session.query(RevivalWorkItem).filter_by(id=data["id"]).first()
    assert db_item.assignee_id == member_user.id


def test_11_non_member_user_cannot_be_assigned(client, db_session, test_user, test_repo, auth_context):
    """11. Non-member user cannot be assigned."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=90005,
        username="non_member_user",
        name="Non Member",
        avatar_url=None,
        access_token="tok_non_member",
    )
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = test_user
    payload = {
        "title": "Invalid assignee task",
        "assignee_id": outsider.id,
    }
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 400
    assert "Assignee must be an active member" in res.json()["detail"]

    # DB not mutated
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_12_nonexistent_user_cannot_be_assigned(client, db_session, test_user, test_repo, auth_context):
    """12. Nonexistent user cannot be assigned."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = test_user
    payload = {
        "title": "Nonexistent assignee task",
        "assignee_id": 999999,
    }
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"

    # DB not mutated
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_13_omitted_assignee_creates_unassigned_item(client, db_session, test_user, test_repo, auth_context):
    """13. Omitted assignee creates an unassigned item."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    payload = {
        "title": "Unassigned item",
    }
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["assignee"] is None

    db_item = db_session.query(RevivalWorkItem).filter_by(id=data["id"]).first()
    assert db_item.assignee_id is None


# ==============================================================================
# 4. LIST TESTS
# ==============================================================================

def test_14_team_owner_can_list_work_items(client, db_session, test_user, test_repo, auth_context):
    """14. Team owner can list work items."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Owner task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Owner task"


def test_15_team_member_can_list_work_items(client, db_session, test_user, test_repo, auth_context):
    """15. Team member can list work items."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90006,
        username="listing_member",
        name="Listing Member",
        avatar_url=None,
        access_token="tok_list",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    item = RevivalWorkItem(team_id=team.id, title="Member visible task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Member visible task"


def test_16_non_member_published_repository_visitor_cannot_list(client, db_session, test_user, test_repo, auth_context):
    """16. Non-member published-repository visitor cannot list work items."""
    test_repo.published = True
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Secret team task")
    db_session.add(item)
    db_session.commit()

    visitor = create_user(
        db=db_session,
        github_id=90007,
        username="visitor_user",
        name="Visitor",
        avatar_url=None,
        access_token="tok_visitor",
    )
    db_session.commit()

    auth_context.user = visitor
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_17_unauthorized_unpublished_repository_user_cannot_list(client, db_session, test_user, test_repo, auth_context):
    """17. Unauthorized unpublished-repository user cannot list work items."""
    test_repo.published = False
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Unpublished private task")
    db_session.add(item)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=90008,
        username="outsider_unpub",
        name="Outsider",
        avatar_url=None,
        access_token="tok_outsider_unpub",
    )
    db_session.commit()

    auth_context.user = outsider
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_18_unauthenticated_user_cannot_list(client, db_session, test_user, test_repo, auth_context):
    """18. Unauthenticated user cannot list work items."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Unauthed check task")
    db_session.add(item)
    db_session.commit()


    auth_context.user = None
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 401
    assert res.json()["detail"] == "Not authenticated"


def test_19_multiple_work_items_returned_in_deterministic_newest_first_order(client, db_session, test_user, test_repo, auth_context):
    """19. Multiple work items are returned in deterministic newest-first order (created_at DESC, id DESC)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    base_time = datetime.utcnow()
    item1 = RevivalWorkItem(team_id=team.id, title="Oldest Item", created_at=base_time - timedelta(minutes=10))
    item2 = RevivalWorkItem(team_id=team.id, title="Middle Item", created_at=base_time - timedelta(minutes=5))
    item3 = RevivalWorkItem(team_id=team.id, title="Newest Item A", created_at=base_time)
    item4 = RevivalWorkItem(team_id=team.id, title="Newest Item B (tie-breaker higher id)", created_at=base_time)
    db_session.add_all([item1, item2, item3, item4])
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4

    titles = [d["title"] for d in data]
    assert titles == [
        "Newest Item B (tie-breaker higher id)",
        "Newest Item A",
        "Middle Item",
        "Oldest Item",
    ]


def test_20_safe_assignee_profile_fields_are_returned(client, db_session, test_user, test_repo, auth_context):
    """20. Safe assignee profile fields are returned."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90009,
        username="safe_dev",
        name="Safe Developer",
        avatar_url="https://avatar.url/safe",
        access_token="super_secret_token_never_expose",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)

    item = RevivalWorkItem(team_id=team.id, title="Task for safe dev", assignee_id=member_user.id)
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assignee = data[0]["assignee"]
    assert assignee == {
        "id": member_user.id,
        "username": "safe_dev",
        "name": "Safe Developer",
        "avatar_url": "https://avatar.url/safe",
    }
    assert "access_token" not in assignee


# ==============================================================================
# 5. PRIVACY TESTS
# ==============================================================================

def test_21_work_items_remain_private_even_when_repository_is_published(client, db_session, test_user, test_repo, auth_context):
    """21. Work items remain private even when repository is published."""
    test_repo.published = True
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Private team task on published repo")
    db_session.add(item)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=90010,
        username="public_visitor",
        name="Visitor",
        avatar_url=None,
        access_token="tok_pub_vis",
    )
    db_session.commit()

    # Visitor can view team because repo is published
    auth_context.user = outsider
    team_res = client.get(f"/repositories/{test_repo.id}/revival-team")
    assert team_res.status_code == 200

    # But visitor CANNOT list work items
    items_res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert items_res.status_code == 404
    assert items_res.json()["detail"] == "Repository not found"

    # And visitor CANNOT create work items
    post_res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json={"title": "Unauthorized"})
    assert post_res.status_code == 404
    assert post_res.json()["detail"] == "Repository not found"


def test_22_no_credentials_or_access_tokens_appear_in_responses(client, db_session, test_user, test_repo, auth_context):
    """22. No credentials/access tokens appear in responses (GET or POST)."""
    test_user.access_token = "owner_secret_oauth_token"
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90011,
        username="member_token_check",
        name="Member Secret",
        avatar_url=None,
        access_token="member_secret_oauth_token",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    auth_context.user = test_user
    # POST check
    post_res = client.post(
        f"/repositories/{test_repo.id}/revival-team/work-items",
        json={"title": "Token audit task", "assignee_id": member_user.id},
    )
    assert post_res.status_code == 201
    post_raw = post_res.text
    assert "owner_secret_oauth_token" not in post_raw
    assert "member_secret_oauth_token" not in post_raw
    assert "access_token" not in post_raw

    # GET check
    get_res = client.get(f"/repositories/{test_repo.id}/revival-team/work-items")
    assert get_res.status_code == 200
    get_raw = get_res.text
    assert "owner_secret_oauth_token" not in get_raw
    assert "member_secret_oauth_token" not in get_raw
    assert "access_token" not in get_raw


# ==============================================================================
# 6. VALIDATION TESTS
# ==============================================================================

def test_23_empty_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """23. Empty title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = test_user
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json={"title": ""})
    assert res.status_code == 422
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_24_whitespace_only_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """24. Whitespace-only title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = test_user
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json={"title": "    \t \n  "})
    assert res.status_code == 422
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_25_overlong_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """25. Overlong title (>200 characters) rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    initial_count = db_session.query(RevivalWorkItem).count()

    auth_context.user = test_user
    res = client.post(f"/repositories/{test_repo.id}/revival-team/work-items", json={"title": "a" * 201})
    assert res.status_code == 422
    assert db_session.query(RevivalWorkItem).count() == initial_count


def test_26_initial_status_cannot_be_arbitrarily_supplied_by_client(client, db_session, test_user, test_repo, auth_context):
    """26. Initial status cannot be arbitrarily supplied by the client."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    # Client passes status="completed" in request body
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/work-items",
        json={"title": "Status tamper task", "status": "completed"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "todo"

    # Confirm in database
    item_in_db = db_session.query(RevivalWorkItem).filter_by(id=data["id"]).first()
    assert item_in_db.status == "todo"


def test_27_invalid_status_is_never_persisted(db_session, test_user, test_repo):
    """27. Invalid status is never persisted (enforced by DB check constraint)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(
        team_id=team.id,
        title="Invalid status task",
        status="bogus_status",
    )
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# 7. INTEGRITY TESTS
# ==============================================================================

def test_28_team_remains_intact_after_work_item_creation(client, db_session, test_user, test_repo, auth_context):
    """28. Team remains intact after work-item creation."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    team_created_at = team.created_at
    team_updated_at = team.updated_at
    team_owner_id = team.owner_id
    team_repo_id = team.repository_id

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/work-items",
        json={"title": "Team integrity check"},
    )
    assert res.status_code == 201

    db_session.refresh(team)
    assert team.id is not None
    assert team.owner_id == team_owner_id
    assert team.repository_id == team_repo_id
    assert team.created_at == team_created_at
    assert len(team.work_items) == 1


def test_29_user_remains_intact_after_work_item_creation(client, db_session, test_user, test_repo, auth_context):
    """29. User remains intact after work-item creation."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=90012,
        username="intact_member",
        name="Intact Member",
        avatar_url="https://avatar.url/intact",
        access_token="intact_token",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    db_session.commit()

    orig_username = member_user.username
    orig_name = member_user.name
    orig_avatar = member_user.avatar_url
    orig_token = member_user.access_token

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/work-items",
        json={"title": "User integrity check", "assignee_id": member_user.id},
    )
    assert res.status_code == 201

    db_session.refresh(member_user)
    assert member_user.username == orig_username
    assert member_user.name == orig_name
    assert member_user.avatar_url == orig_avatar
    assert member_user.access_token == orig_token


def test_30_revival_request_remains_unaffected(client, db_session, test_user, test_repo, auth_context):
    """30. RevivalRequest remains unaffected by work-item operations."""
    requester = create_user(
        db=db_session,
        github_id=90013,
        username="req_user",
        name="Requester",
        avatar_url=None,
        access_token="tok_req",
    )
    db_session.commit()

    req = RevivalRequest(
        repository_id=test_repo.id,
        requester_id=requester.id,
        message="Please let me join",
        status="approved",
    )
    db_session.add(req)

    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    member = RevivalTeamMember(team_id=team.id, user_id=requester.id)
    db_session.add(member)
    db_session.commit()


    req_id = req.id
    req_status = req.status
    req_msg = req.message

    auth_context.user = test_user
    res = client.post(
        f"/repositories/{test_repo.id}/revival-team/work-items",
        json={"title": "Work item alongside request", "assignee_id": requester.id},
    )
    assert res.status_code == 201

    db_session.refresh(req)
    assert req.id == req_id
    assert req.status == req_status
    assert req.message == req_msg
    assert req.repository_id == test_repo.id
    assert req.requester_id == requester.id


# ==============================================================================
# 8. PATCH - OWNER TESTS
# ==============================================================================

def test_31_owner_can_update_title(client, db_session, test_user, test_repo, auth_context):
    """31. Team owner can update title."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Old Title", description="Desc")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Updated Title"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == item.id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Desc"

    db_session.refresh(item)
    assert item.title == "Updated Title"


def test_32_owner_can_update_description(client, db_session, test_user, test_repo, auth_context):
    """32. Team owner can update description or clear it."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Title", description="Initial description")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"description": "Changed description"},
    )
    assert res.status_code == 200
    assert res.json()["description"] == "Changed description"

    # Explicit null to clear description
    res_null = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"description": None},
    )
    assert res_null.status_code == 200
    assert res_null.json()["description"] is None

    db_session.refresh(item)
    assert item.description is None


def test_33_owner_can_assign_member(client, db_session, test_user, test_repo, auth_context):
    """33. Team owner can assign an active member."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91001,
        username="active_member_33",
        name="Active Member",
        avatar_url="https://avatar.url/33",
        access_token="tok_33",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Assign Task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": member_user.id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["assignee"] is not None
    assert data["assignee"]["id"] == member_user.id
    assert data["assignee"]["username"] == "active_member_33"
    assert data["assignee"]["name"] == "Active Member"


def test_34_owner_can_assign_team_owner(client, db_session, test_user, test_repo, auth_context):
    """34. Team owner can assign themselves (team owner is eligible)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Self-assigned task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": test_user.id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["assignee"] is not None
    assert data["assignee"]["id"] == test_user.id


def test_35_owner_can_unassign(client, db_session, test_user, test_repo, auth_context):
    """35. Team owner can unassign a work item by passing null."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Unassign task", assignee_id=test_user.id)
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": None},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["assignee"] is None

    db_session.refresh(item)
    assert item.assignee_id is None


def test_36_owner_can_change_status(client, db_session, test_user, test_repo, auth_context):
    """36. Team owner can change status."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Status task", status="todo")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"status": "in_progress"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"

    res2 = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"status": "completed"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "completed"


def test_37_owner_can_update_multiple_allowed_fields_together(client, db_session, test_user, test_repo, auth_context):
    """37. Team owner can update multiple allowed fields simultaneously."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91002,
        username="multi_member",
        name="Multi Member",
        avatar_url=None,
        access_token="tok_multi",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Original Title", description="Old Desc", status="todo")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    payload = {
        "title": "Combined Update Title",
        "description": "Combined Update Desc",
        "assignee_id": member_user.id,
        "status": "in_progress",
    }
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Combined Update Title"
    assert data["description"] == "Combined Update Desc"
    assert data["status"] == "in_progress"
    assert data["assignee"]["id"] == member_user.id


def test_38_updated_at_changes_after_successful_update(client, db_session, test_user, test_repo, auth_context):
    """38. updated_at changes after a successful PATCH update."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    past_time = datetime.utcnow() - timedelta(hours=2)
    item = RevivalWorkItem(
        team_id=team.id,
        title="Time check task",
        created_at=past_time,
        updated_at=past_time,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    old_updated_at = item.updated_at

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Time check updated"},
    )
    assert res.status_code == 200

    db_session.refresh(item)
    assert item.updated_at > old_updated_at


# ==============================================================================
# 9. PATCH - MEMBER PERMISSION TESTS
# ==============================================================================

def test_39_member_can_change_status(client, db_session, test_user, test_repo, auth_context):
    """39. Active team member can change status."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91003,
        username="member_status_updater",
        name="Updater",
        avatar_url=None,
        access_token="tok_updater",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Member can update status", status="todo")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"status": "in_progress"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"

    db_session.refresh(item)
    assert item.status == "in_progress"


def test_40_member_cannot_change_title(client, db_session, test_user, test_repo, auth_context):
    """40. Active member cannot change title (rejected with 403)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91004,
        username="member_no_title",
        name="No Title",
        avatar_url=None,
        access_token="tok_nt",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Protected Title", status="todo")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Unauthorized Title Change"},
    )
    assert res.status_code == 403
    assert "Members are only permitted to update status" in res.json()["detail"]

    db_session.refresh(item)
    assert item.title == "Protected Title"


def test_41_member_cannot_change_description(client, db_session, test_user, test_repo, auth_context):
    """41. Active member cannot change description (rejected with 403)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91005,
        username="member_no_desc",
        name="No Desc",
        avatar_url=None,
        access_token="tok_nd",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Title", description="Protected Description")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"description": "Unauthorized Description Change"},
    )
    assert res.status_code == 403

    db_session.refresh(item)
    assert item.description == "Protected Description"


def test_42_member_cannot_change_assignee(client, db_session, test_user, test_repo, auth_context):
    """42. Active member cannot change assignee (rejected with 403)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91006,
        username="member_no_assignee",
        name="No Assignee",
        avatar_url=None,
        access_token="tok_na",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Title", assignee_id=None)
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": member_user.id},
    )
    assert res.status_code == 403

    db_session.refresh(item)
    assert item.assignee_id is None


def test_43_member_cannot_bypass_permissions_with_status_and_forbidden_field(client, db_session, test_user, test_repo, auth_context):
    """43. Member cannot bypass permissions by submitting status + forbidden field together."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91007,
        username="member_bypass_attempt",
        name="Bypass Attempt",
        avatar_url=None,
        access_token="tok_bp",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Safe Title", description="Safe Desc", status="todo")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    payload = {
        "status": "completed",
        "title": "Malicious Title Change",
    }
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json=payload,
    )
    assert res.status_code == 403

    db_session.refresh(item)
    assert item.title == "Safe Title"
    assert item.status == "todo"


# ==============================================================================
# 10. ASSIGNEE VALIDATION TESTS
# ==============================================================================

def test_44_owner_cannot_assign_outsider(client, db_session, test_user, test_repo, auth_context):
    """44. Owner cannot assign a user who is not an active member of the same revival team."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    outsider = create_user(
        db=db_session,
        github_id=91008,
        username="outsider_assignee",
        name="Outsider",
        avatar_url=None,
        access_token="tok_out",
    )
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Outsider assign task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": outsider.id},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Assignee must be an active member of the revival team."

    db_session.refresh(item)
    assert item.assignee_id is None


def test_45_owner_cannot_assign_nonexistent_user(client, db_session, test_user, test_repo, auth_context):
    """45. Owner cannot assign a nonexistent user ID."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Nonexistent assign task")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": 999999},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


# ==============================================================================
# 11. STATUS VALIDATION TESTS
# ==============================================================================

def test_46_status_allowed_values(client, db_session, test_user, test_repo, auth_context):
    """46. Status accepts 'todo', 'in_progress', and 'completed'."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Status transitions")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    for st in ["in_progress", "completed", "todo"]:
        res = client.patch(
            f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
            json={"status": st},
        )
        assert res.status_code == 200
        assert res.json()["status"] == st


def test_47_invalid_status_rejected_with_422(client, db_session, test_user, test_repo, auth_context):
    """47. Invalid status rejected with 422 Unprocessable Entity."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Invalid status check")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"status": "invalid_status"},
    )
    assert res.status_code == 422


# ==============================================================================
# 12. PAYLOAD & FIELD VALIDATION TESTS
# ==============================================================================

def test_48_blank_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """48. Blank title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": ""},
    )
    assert res.status_code == 422


def test_49_whitespace_only_title_rejected(client, db_session, test_user, test_repo, auth_context):
    """49. Whitespace-only title rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "   \t \n  "},
    )
    assert res.status_code == 422


def test_50_title_exceeding_max_length_rejected(client, db_session, test_user, test_repo, auth_context):
    """50. Title exceeding 200 characters rejected with 422."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "a" * 201},
    )
    assert res.status_code == 422


def test_51_empty_patch_rejected(client, db_session, test_user, test_repo, auth_context):
    """51. Empty PATCH payload rejected with 400."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={},
    )
    assert res.status_code == 400
    assert "No fields provided for update" in res.json()["detail"]


# ==============================================================================
# 13. AUTHORIZATION & PRIVACY TESTS
# ==============================================================================

def test_52_unauthenticated_patch_denied(client, db_session, test_user, test_repo, auth_context):
    """52. Unauthenticated PATCH returns 401."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = None
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Unauth change"},
    )
    assert res.status_code == 401


def test_53_outsider_patch_denied(client, db_session, test_user, test_repo, auth_context):
    """53. Outsider PATCH returns 404 Repository not found (privacy preserved)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)

    outsider = create_user(
        db=db_session,
        github_id=91009,
        username="outsider_patcher",
        name="Outsider",
        avatar_url=None,
        access_token="tok_out_p",
    )
    db_session.commit()

    auth_context.user = outsider
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Outsider change"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_54_repository_owner_who_is_not_team_member_cannot_patch(client, db_session, test_user, test_repo, auth_context):
    """54. Repository owner who is not team owner or team member cannot PATCH."""
    different_team_owner = create_user(
        db=db_session,
        github_id=91010,
        username="lead_owner",
        name="Lead Owner",
        avatar_url=None,
        access_token="tok_lo",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=test_repo.id, owner_id=different_team_owner.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Lead's item")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user  # repo owner
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"title": "Repo owner trying to edit"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_55_unauthenticated_delete_denied(client, db_session, test_user, test_repo, auth_context):
    """55. Unauthenticated DELETE returns 401."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = None
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 401


def test_56_outsider_delete_denied(client, db_session, test_user, test_repo, auth_context):
    """56. Outsider DELETE returns 404 Repository not found (privacy preserved)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)

    outsider = create_user(
        db=db_session,
        github_id=91011,
        username="outsider_deleter",
        name="Outsider",
        avatar_url=None,
        access_token="tok_out_d",
    )
    db_session.commit()

    auth_context.user = outsider
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_57_non_owner_team_member_cannot_delete(client, db_session, test_user, test_repo, auth_context):
    """57. Active non-owner team member cannot DELETE (privacy preserved with 404)."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91012,
        username="member_deleter",
        name="Member Deleter",
        avatar_url=None,
        access_token="tok_md",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Initial Title")
    db_session.add(item)
    db_session.commit()

    auth_context.user = member_user
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_58_repository_owner_who_is_not_team_owner_cannot_delete(client, db_session, test_user, test_repo, auth_context):
    """58. Repository owner who is not the team owner cannot DELETE."""
    different_team_owner = create_user(
        db=db_session,
        github_id=91013,
        username="lead_owner_del",
        name="Lead Owner",
        avatar_url=None,
        access_token="tok_lod",
    )
    db_session.commit()

    team = RevivalTeam(repository_id=test_repo.id, owner_id=different_team_owner.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Lead's item to delete")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user  # repo owner
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Repository not found"


def test_59_wrong_repository_work_item_combination_denied(client, db_session, test_user, test_repo, auth_context):
    """59. Work item belonging to repo 1 cannot be patched or deleted via repo 2's endpoint."""
    repo2 = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 99999,
            "name": "repo-two",
            "full_name": f"{test_user.username}/repo-two",
            "html_url": f"https://github.com/{test_user.username}/repo-two",
            "default_branch": "main",
        },
    )
    team1 = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    team2 = RevivalTeam(repository_id=repo2.id, owner_id=test_user.id)
    db_session.add_all([team1, team2])
    db_session.commit()


    item_repo1 = RevivalWorkItem(team_id=team1.id, title="Item in team 1")
    db_session.add(item_repo1)
    db_session.commit()

    auth_context.user = test_user
    # Attempt PATCH item 1 via repo 2 endpoint -> 404
    res_patch = client.patch(
        f"/repositories/{repo2.id}/revival-team/work-items/{item_repo1.id}",
        json={"title": "Cross-repo patch attempt"},
    )
    assert res_patch.status_code == 404
    assert res_patch.json()["detail"] == "Work item not found"

    # Attempt DELETE item 1 via repo 2 endpoint -> 404
    res_del = client.delete(f"/repositories/{repo2.id}/revival-team/work-items/{item_repo1.id}")
    assert res_del.status_code == 404
    assert res_del.json()["detail"] == "Work item not found"


def test_60_nonexistent_work_item_returns_404(client, db_session, test_user, test_repo, auth_context):
    """60. Nonexistent work item ID returns 404."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    auth_context.user = test_user
    res_patch = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/999999",
        json={"title": "Does not exist"},
    )
    assert res_patch.status_code == 404
    assert res_patch.json()["detail"] == "Work item not found"

    res_del = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/999999")
    assert res_del.status_code == 404
    assert res_del.json()["detail"] == "Work item not found"


# ==============================================================================
# 14. DELETE & INTEGRITY TESTS
# ==============================================================================

def test_61_owner_can_delete_work_item(client, db_session, test_user, test_repo, auth_context):
    """61. Team owner can delete work item; returns 204 No Content with empty body."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Item to delete")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 204
    assert res.text == ""


def test_62_deleted_work_item_is_gone_from_db(client, db_session, test_user, test_repo, auth_context):
    """62. Deleted work item is actually removed from the database."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    item = RevivalWorkItem(team_id=team.id, title="Item gone check")
    db_session.add(item)
    db_session.commit()
    item_id = item.id

    auth_context.user = test_user
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item_id}")
    assert res.status_code == 204

    db_item = db_session.query(RevivalWorkItem).filter_by(id=item_id).first()
    assert db_item is None


def test_63_delete_work_item_preserves_team_and_members(client, db_session, test_user, test_repo, auth_context):
    """63. Deleting a work item does not delete or alter the team or its members."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91014,
        username="safe_member",
        name="Safe Member",
        avatar_url=None,
        access_token="tok_safe",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Delete won't cascade to team", assignee_id=member_user.id)
    db_session.add(item)
    db_session.commit()

    team_id = team.id
    member_id = member.id
    user_id = member_user.id

    auth_context.user = test_user
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 204

    db_session.expire_all()
    assert db_session.query(RevivalTeam).filter_by(id=team_id).first() is not None
    assert db_session.query(RevivalTeamMember).filter_by(id=member_id).first() is not None
    assert db_session.query(User).filter_by(id=user_id).first() is not None


def test_64_delete_work_item_preserves_repository_and_revival_request(client, db_session, test_user, test_repo, auth_context):
    """64. Deleting a work item does not delete or alter the repository or revival requests."""
    requester = create_user(
        db=db_session,
        github_id=91015,
        username="req_user_64",
        name="Requester 64",
        avatar_url=None,
        access_token="tok_req_64",
    )
    db_session.commit()

    req = RevivalRequest(
        repository_id=test_repo.id,
        requester_id=requester.id,
        message="I want to revive",
        status="approved",
    )
    db_session.add(req)
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    item = RevivalWorkItem(team_id=team.id, title="Item beside request")
    db_session.add(item)
    db_session.commit()

    req_id = req.id
    repo_id = test_repo.id

    auth_context.user = test_user
    res = client.delete(f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}")
    assert res.status_code == 204

    db_session.expire_all()
    assert db_session.query(Repository).filter_by(id=repo_id).first() is not None
    assert db_session.query(RevivalRequest).filter_by(id=req_id).first() is not None


def test_65_response_contains_only_safe_fields(client, db_session, test_user, test_repo, auth_context):
    """65. Response contains only safe fields; no access_token, credentials, or internal secrets."""
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()

    member_user = create_user(
        db=db_session,
        github_id=91016,
        username="secret_check_user",
        name="Secret Check",
        avatar_url="https://avatar.url/secret",
        access_token="SUPER_SECRET_GITHUB_ACCESS_TOKEN_12345",
    )
    member = RevivalTeamMember(team_id=team.id, user_id=member_user.id)
    db_session.add(member)
    item = RevivalWorkItem(team_id=team.id, title="Security check item")
    db_session.add(item)
    db_session.commit()

    auth_context.user = test_user
    res = client.patch(
        f"/repositories/{test_repo.id}/revival-team/work-items/{item.id}",
        json={"assignee_id": member_user.id},
    )
    assert res.status_code == 200
    res_text = res.text
    assert "SUPER_SECRET_GITHUB_ACCESS_TOKEN_12345" not in res_text
    assert "access_token" not in res_text

    data = res.json()
    assignee = data["assignee"]
    assert set(assignee.keys()) == {"id", "username", "name", "avatar_url"}
