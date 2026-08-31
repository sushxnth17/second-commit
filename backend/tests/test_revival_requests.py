import pytest
from app.models.repository import Repository
from app.models.revival_request import RevivalRequest
from app.services.repository_service import create_repository
from app.services.user_service import create_user


def test_create_revival_request_lifecycle(client, db_session, test_user, auth_context):
    # 1. Create developer_b user
    developer_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    db_session.commit()

    # 2. Create repository owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 901,
            "name": "project-alpha",
            "full_name": "testuser/project-alpha",
            "html_url": "https://github.com/testuser/project-alpha",
            "default_branch": "main",
        },
    )
    # Publish repository
    repo.published = True
    db_session.commit()

    # 3. Request to revive as Developer B (Authenticated, Not Owner, Published)
    auth_context.user = developer_b
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "I would love to help continue maintaining this project!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["repository_id"] == repo.id
    assert data["requester_id"] == developer_b.id
    assert data["message"] == "I would love to help continue maintaining this project!"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # 4. Check if request is persisted in the database
    db_req = db_session.query(RevivalRequest).filter(RevivalRequest.id == data["id"]).first()
    assert db_req is not None
    assert db_req.repository_id == repo.id
    assert db_req.requester_id == developer_b.id
    assert db_req.message == "I would love to help continue maintaining this project!"
    assert db_req.status == "pending"

    # 5. Check GET my-pending endpoint
    response = client.get(f"/repositories/{repo.id}/revival-requests/my-pending")
    assert response.status_code == 200
    get_data = response.json()
    assert get_data is not None
    assert get_data["id"] == data["id"]
    assert get_data["status"] == "pending"


def test_revival_request_validation_rules(client, db_session, test_user, auth_context):
    # Setup Developer B
    developer_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    # Setup Developer C
    developer_c = create_user(
        db=db_session,
        github_id=98766,
        username="devc",
        name="Developer C",
        avatar_url="https://avatar.url/c",
        access_token="token_c",
    )
    
    # Create repository owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 902,
            "name": "project-beta",
            "full_name": "testuser/project-beta",
            "html_url": "https://github.com/testuser/project-beta",
            "default_branch": "main",
        },
    )
    db_session.commit()

    # Rule 5: Unauthenticated user cannot create a request
    auth_context.user = None
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Hack attempt"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Rule 6: Developer cannot request their own repository
    auth_context.user = test_user
    # Publish first to isolate the owner check
    repo.published = True
    db_session.commit()
    
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "My own repo"},
    )
    assert response.status_code == 400
    assert "own repository" in response.json()["detail"]

    # Rule 7: Developer cannot request an unpublished repository
    # Unpublish it
    repo.published = False
    db_session.commit()

    auth_context.user = developer_b
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Unpublished project request"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"

    # Rule 8: Duplicate pending request is rejected
    # Publish it again
    repo.published = True
    db_session.commit()

    # Create first request
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "First request"},
    )
    assert response.status_code == 201

    # Try creating second request
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Second duplicate request"},
    )
    assert response.status_code == 409
    assert "already have" in response.json()["detail"]

    # Rule 9: Different developers can each request the same published repository
    auth_context.user = developer_c
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Request from Dev C"},
    )
    assert response.status_code == 201
    assert response.json()["requester_id"] == developer_c.id

    # Rule 10: Missing repository returns appropriate error
    response = client.post(
        "/repositories/99999/revival-requests",
        json={"message": "Non-existent repo"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
