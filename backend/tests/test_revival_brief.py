import pytest
from app.models.repository import Repository
from app.models.revival_brief import RevivalBrief
from app.services.repository_service import create_repository


def test_revival_brief_lifecycle(client, db_session, test_user):
    # 1. Create a repository
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 501,
            "name": "brief-repo",
            "full_name": "testuser/brief-repo",
            "html_url": "https://github.com/testuser/brief-repo",
            "default_branch": "main",
        },
    )
    db_session.commit()

    # 2. Get handover (should return null/None)
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 200
    assert response.json() is None

    # 3. Create a handover brief (PUT)
    response = client.put(
        f"/repositories/{repo.id}/handover",
        json={
            "developer_notes": "First developer notes",
            "revival_intent": "takeover",
            "status": "draft",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["developer_notes"] == "First developer notes"
    assert data["revival_intent"] == "takeover"
    assert data["status"] == "draft"

    # 4. Get handover brief (GET)
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 200
    data = response.json()
    assert data["developer_notes"] == "First developer notes"
    assert data["revival_intent"] == "takeover"
    assert data["status"] == "draft"

    # 5. Update handover brief (PUT)
    response = client.put(
        f"/repositories/{repo.id}/handover",
        json={
            "developer_notes": "Updated developer notes",
            "status": "prepared",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["developer_notes"] == "Updated developer notes"
    assert data["revival_intent"] == "takeover"  # remains unchanged
    assert data["status"] == "prepared"

    # 6. Delete/Reset handover brief (DELETE)
    response = client.delete(f"/repositories/{repo.id}/handover")
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # 7. Get handover brief again (GET should be null/None)
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 200
    assert response.json() is None


def test_revival_brief_security(client, db_session, test_user, auth_context):
    from app.services.user_service import create_user
    test_user_2 = create_user(
        db=db_session,
        github_id=67890,
        username="testuser2",
        name="Test User 2",
        avatar_url="https://avatar.url/2",
        access_token="test_token_2",
    )
    # User 1 owns the repo
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 502,
            "name": "security-repo",
            "full_name": "testuser/security-repo",
            "html_url": "https://github.com/testuser/security-repo",
            "default_branch": "main",
        },
    )
    db_session.commit()

    # User 1 creates and prepares the brief
    response = client.put(
        f"/repositories/{repo.id}/handover",
        json={
            "developer_notes": "Top secret notes",
            "revival_intent": "archive",
            "status": "prepared",
        },
    )
    assert response.status_code == 200

    # User 2 attempts to get it (should be 404 since repo is not published)
    auth_context.user = test_user_2
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 404

    # User 2 attempts to update/PUT it (should be 403 Forbidden)
    response = client.put(
        f"/repositories/{repo.id}/handover",
        json={"developer_notes": "Hacked"},
    )
    assert response.status_code == 403

    # User 2 attempts to delete it (should be 403 Forbidden)
    response = client.delete(f"/repositories/{repo.id}/handover")
    assert response.status_code == 403

    # Log back in as User 1 and publish the repo
    auth_context.user = test_user
    response = client.post(f"/repositories/{repo.id}/publish")
    assert response.status_code == 200

    # User 2 attempts to get it again (should succeed now that it's published!)
    auth_context.user = test_user_2
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 200
    assert response.json()["developer_notes"] == "Top secret notes"

    # User 2 still cannot update it even if published
    response = client.put(
        f"/repositories/{repo.id}/handover",
        json={"developer_notes": "Hacked"},
    )
    assert response.status_code == 403

    # User 2 still cannot delete it even if published
    response = client.delete(f"/repositories/{repo.id}/handover")
    assert response.status_code == 403

    # User 1 unpublishes the repo
    auth_context.user = test_user
    response = client.post(f"/repositories/{repo.id}/unpublish")
    assert response.status_code == 200

    # User 2 can no longer access it (should be 404)
    auth_context.user = test_user_2
    response = client.get(f"/repositories/{repo.id}/handover")
    assert response.status_code == 404


def test_revival_brief_unauthenticated(client, auth_context):
    # Set unauthenticated
    auth_context.user = None

    response = client.get("/repositories/123/handover")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
