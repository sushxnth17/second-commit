from datetime import datetime, timezone, timedelta
from app.services.user_service import create_user
from app.services.repository_service import create_repository
from app.services.dormancy_service import calculate_dormancy


def test_calculate_dormancy(db_session):
    user = create_user(
        db=db_session,
        github_id=33333,
        username="dormancyuser",
        name="Dormancy User",
        avatar_url="https://avatar.url",
        access_token="dormancy_token",
    )

    # 1. Active: pushed 5 days ago
    repo_active = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 801,
            "name": "active-repo",
            "full_name": "dormancyuser/active-repo",
            "html_url": "https://github.com/dormancyuser/active-repo",
            "default_branch": "main",
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    )
    days, status, message = calculate_dormancy(repo_active)
    assert days == 5
    assert status == "Active"
    assert "actively maintained" in message

    # 2. Slowing Down: pushed 45 days ago
    repo_slowing = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 802,
            "name": "slowing-repo",
            "full_name": "dormancyuser/slowing-repo",
            "html_url": "https://github.com/dormancyuser/slowing-repo",
            "default_branch": "main",
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
        },
    )
    days, status, message = calculate_dormancy(repo_slowing)
    assert days == 45
    assert status == "Slowing Down"
    assert "Activity has slowed down" in message

    # 3. Dormant: pushed 120 days ago
    repo_dormant = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 803,
            "name": "dormant-repo",
            "full_name": "dormancyuser/dormant-repo",
            "html_url": "https://github.com/dormancyuser/dormant-repo",
            "default_branch": "main",
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
        },
    )
    days, status, message = calculate_dormancy(repo_dormant)
    assert days == 120
    assert status == "Dormant"
    assert "dormant" in message

    # 4. Archived Candidate: pushed 200 days ago
    repo_archived = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 804,
            "name": "archived-repo",
            "full_name": "dormancyuser/archived-repo",
            "html_url": "https://github.com/dormancyuser/archived-repo",
            "default_branch": "main",
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(),
        },
    )
    days, status, message = calculate_dormancy(repo_archived)
    assert days == 200
    assert status == "Archived Candidate"
    assert "candidate for archiving" in message


def test_get_repository_dormancy_endpoint(client, db_session):
    user = create_user(
        db=db_session,
        github_id=44444,
        username="dormancyapiuser",
        name="Dormancy API User",
        avatar_url="https://avatar.url",
        access_token="dormancy_api_token",
    )

    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 805,
            "name": "api-dormancy-repo",
            "full_name": "dormancyapiuser/api-dormancy-repo",
            "html_url": "https://github.com/dormancyapiuser/api-dormancy-repo",
            "default_branch": "main",
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        },
    )

    response = client.get(f"/repositories/{repo.id}/dormancy")
    assert response.status_code == 200

    data = response.json()
    assert data["repository_id"] == repo.id
    assert data["repository_name"] == "api-dormancy-repo"
    assert data["days_since_last_push"] == 10
    assert data["status"] == "Active"
    assert "actively maintained" in data["message"]


def test_get_repository_dormancy_not_found(client):
    response = client.get("/repositories/999999/dormancy")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
