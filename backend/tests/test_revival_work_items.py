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
