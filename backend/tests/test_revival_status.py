import os
import tempfile
import pytest
from alembic import command
from alembic.config import Config
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.models.repository import Repository
from app.models.revival_team import RevivalTeam
from app.models.revival_work_item import RevivalWorkItem
from app.models.user import User
from app.services.user_service import create_user
from app.services.repository_service import create_repository


# ==========================================
# MODEL TESTS
# ==========================================

def test_model_defaults_to_seeking_revival(db_session, test_user):
    """Test that newly instantiated and persisted Repository defaults to seeking_revival."""
    repo = Repository(
        github_repo_id=99001,
        name="test-default-repo",
        full_name="testuser/test-default-repo",
        default_branch="main",
        html_url="https://github.com/testuser/test-default-repo",
        owner_id=test_user.id,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    assert repo.revival_status == "seeking_revival"


def test_model_status_persists(db_session, test_user):
    """Test that valid statuses persist to the database."""
    repo = Repository(
        github_repo_id=99002,
        name="test-persist-repo",
        full_name="testuser/test-persist-repo",
        default_branch="main",
        html_url="https://github.com/testuser/test-persist-repo",
        owner_id=test_user.id,
        revival_status="forming_team",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    assert repo.revival_status == "forming_team"

    repo.revival_status = "revival_in_progress"
    db_session.commit()
    db_session.refresh(repo)

    assert repo.revival_status == "revival_in_progress"


def test_model_check_constraint_rejects_invalid_status(db_session, test_user):
    """Test that SQLite check constraint rejects invalid persisted revival_status values."""
    repo = Repository(
        github_repo_id=99003,
        name="test-invalid-repo",
        full_name="testuser/test-invalid-repo",
        default_branch="main",
        html_url="https://github.com/testuser/test-invalid-repo",
        owner_id=test_user.id,
        revival_status="invalid_custom_status",
    )
    db_session.add(repo)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==========================================
# MIGRATION TESTS
# ==========================================

def test_migration_lifecycle():
    """
    Test full Alembic migration lifecycle:
    1. Upgrade to down_revision (65f873eebc8b)
    2. Insert pre-existing repository row
    3. Upgrade to head (7a1f2e8c9b04)
    4. Confirm existing row receives 'seeking_revival' and column is non-null
    5. Confirm CHECK constraint works
    6. Downgrade cleanly to 65f873eebc8b
    7. Re-upgrade cleanly to head
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade to previous head
        command.upgrade(alembic_cfg, "65f873eebc8b")

        # 2. Insert user and repository row without revival_status column
        engine = sa.create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(sa.text("INSERT INTO users (id, github_id, username) VALUES (1, 100, 'miguser')"))
            conn.execute(sa.text(
                "INSERT INTO repositories (id, github_repo_id, name, full_name, html_url, default_branch, owner_id, published) "
                "VALUES (1, 101, 'migrepo', 'miguser/migrepo', 'https://github.com/miguser/migrepo', 'main', 1, 0)"
            ))
            conn.commit()

        # 3. Upgrade to new revision head
        command.upgrade(alembic_cfg, "head")

        # 4. Confirm row receives 'seeking_revival'
        with engine.connect() as conn:
            val = conn.execute(sa.text("SELECT revival_status FROM repositories WHERE id = 1")).scalar()
            assert val == "seeking_revival"

            # Verify check constraint
            with pytest.raises(Exception):
                conn.execute(sa.text("UPDATE repositories SET revival_status = 'bad_status' WHERE id = 1"))
                conn.commit()

        # 5. Downgrade cleanly
        command.downgrade(alembic_cfg, "65f873eebc8b")

        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(sa.text("SELECT revival_status FROM repositories WHERE id = 1"))

        # 6. Re-upgrade cleanly
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            val = conn.execute(sa.text("SELECT revival_status FROM repositories WHERE id = 1")).scalar()
            assert val == "seeking_revival"

    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass


# ==========================================
# API ENDPOINT & VALID STATUSES TESTS
# ==========================================

@pytest.mark.parametrize("status", [
    "seeking_revival",
    "forming_team",
    "revival_in_progress",
    "revived",
    "paused",
    "archived",
])
def test_owner_can_update_to_all_valid_statuses(client, test_repo, auth_context, test_user, status):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": status})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_repo.id
    assert data["revival_status"] == status


# ==========================================
# VALIDATION TESTS (HTTP 422)
# ==========================================

@pytest.mark.parametrize("invalid_status", [
    "invalid_status",
    "active",
    "todo",
    "in_progress",
    "completed",
    "SEEKING_REVIVAL",
    "",
    "   ",
])
def test_invalid_status_rejected_with_422(client, test_repo, auth_context, test_user, invalid_status):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": invalid_status})
    assert response.status_code == 422


def test_empty_payload_rejected_with_422(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={})
    assert response.status_code == 422


def test_null_status_rejected_with_422(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": None})
    assert response.status_code == 422


# ==========================================
# AUTHORIZATION TESTS
# ==========================================

def test_unauthenticated_update_rejected(client, test_repo, auth_context):
    auth_context.user = None
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": "forming_team"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_non_owner_update_forbidden(client, test_repo, auth_context, db_session):
    other_user = create_user(
        db=db_session,
        github_id=88888,
        username="otheruser",
        name="Other User",
        avatar_url="https://avatar.url/other",
        access_token="other_token",
    )
    auth_context.user = other_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": "forming_team"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Repository owned by another user"


def test_nonexistent_repository_returns_404(client, auth_context, test_user):
    auth_context.user = test_user
    url = "/repositories/999999/revival-status"

    response = client.patch(url, json={"status": "forming_team"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


# ==========================================
# PERSISTENCE TESTS
# ==========================================

def test_update_persists_across_db_refresh(client, test_repo, auth_context, test_user, db_session):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    res = client.patch(url, json={"status": "revived"})
    assert res.status_code == 200

    # Expire and refresh session to verify persistence in database
    db_session.expire_all()
    fresh_repo = db_session.query(Repository).filter(Repository.id == test_repo.id).first()
    assert fresh_repo.revival_status == "revived"


# ==========================================
# REGRESSION & INTEGRATION TESTS
# ==========================================

def test_repository_get_exposes_revival_status(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    res = client.get(f"/repositories/{test_repo.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["revival_status"] == "seeking_revival"
    assert data["owner_id"] == test_user.id


def test_repository_list_exposes_revival_status(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    res = client.get("/repositories")
    assert res.status_code == 200
    data = res.json()
    repo_item = next(r for r in data if r["id"] == test_repo.id)
    assert repo_item["revival_status"] == "seeking_revival"
    assert repo_item["owner_id"] == test_user.id


def test_discover_repositories_exposes_revival_status(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    # Publish repository so discover endpoint returns it
    client.post(f"/repositories/{test_repo.id}/publish")

    res = client.get("/repositories/discover")
    assert res.status_code == 200
    data = res.json()
    repo_item = next(r for r in data if r["id"] == test_repo.id)
    assert repo_item["revival_status"] == "seeking_revival"
    assert repo_item["published"] is True


def test_revival_team_and_work_items_intact_and_no_auto_transition(client, test_repo, auth_context, test_user, db_session):
    """
    CRITICAL PRODUCT RULE:
    Creating a team, approving requests, creating work items must NOT automatically change revival_status!
    Status changes remain strictly manual.
    """
    auth_context.user = test_user

    # 1. Initial status is seeking_revival
    assert test_repo.revival_status == "seeking_revival"

    # 2. Create revival team
    team = RevivalTeam(repository_id=test_repo.id, owner_id=test_user.id)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(test_repo)
    # MUST still be seeking_revival
    assert test_repo.revival_status == "seeking_revival"

    # 3. Create work item
    item = RevivalWorkItem(team_id=team.id, title="Initial task")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(test_repo)
    # MUST still be seeking_revival
    assert test_repo.revival_status == "seeking_revival"

    # 4. Now manually update status via PATCH
    url = f"/repositories/{test_repo.id}/revival-status"
    patch_res = client.patch(url, json={"status": "revival_in_progress"})
    assert patch_res.status_code == 200
    assert patch_res.json()["revival_status"] == "revival_in_progress"

    db_session.refresh(test_repo)
    assert test_repo.revival_status == "revival_in_progress"


# ==========================================
# SECURITY TESTS
# ==========================================

def test_response_does_not_leak_secrets(client, test_repo, auth_context, test_user):
    auth_context.user = test_user
    url = f"/repositories/{test_repo.id}/revival-status"

    response = client.patch(url, json={"status": "paused"})
    assert response.status_code == 200
    data = response.json()

    assert "access_token" not in data
    assert "token" not in data
    assert "secret" not in data
    assert "github_client_secret" not in data

    if data.get("owner"):
        assert "access_token" not in data["owner"]
        assert "token" not in data["owner"]
