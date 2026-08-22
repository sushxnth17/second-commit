from datetime import datetime, timezone, timedelta
from app.services.user_service import create_user
from app.services.repository_service import create_repository
from app.services.health_service import calculate_health_score


def test_calculate_health_score(db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=11111,
        username="healthtester",
        name="Health Tester",
        avatar_url="https://avatar.url",
        access_token="health_token",
    )

    # 2. Create a repository with specific values to score
    # Stars (20): 100 stars -> 20 pts
    # Forks (10): 25 forks -> 8 pts
    # Open Issues (15): 5 issues -> 12 pts
    # Recent Activity (30): push 5 days ago -> 30 pts
    # Size (5): 1500 size -> 5 pts
    # Description (5): "A very good description longer than 10 chars" -> 5 pts
    # Default Branch (5): "main" -> 5 pts
    # Language (10): "Python" -> 10 pts
    # Total expected: 20 + 8 + 12 + 30 + 5 + 5 + 5 + 10 = 95 (Grade A)
    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 901,
            "name": "good-repo",
            "full_name": "healthtester/good-repo",
            "description": "A very good description longer than 10 chars",
            "html_url": "https://github.com/healthtester/good-repo",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 100,
            "forks_count": 25,
            "open_issues_count": 5,
            "size": 1500,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    )

    score, grade, summary = calculate_health_score(repo)
    assert score == 95
    assert grade == "A"
    assert "excellent health" in summary


def test_get_repository_health_endpoint(client, db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=22222,
        username="apihealthtester",
        name="API Health Tester",
        avatar_url="https://avatar.url",
        access_token="api_health_token",
    )

    # 2. Create a repository
    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 902,
            "name": "api-repo",
            "full_name": "apihealthtester/api-repo",
            "description": "Short",
            "html_url": "https://github.com/apihealthtester/api-repo",
            "language": None,
            "default_branch": "develop",
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 50,
            "size": 0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
        },
    )

    # 3. Call endpoint
    response = client.get(f"/repositories/{repo.id}/health")
    assert response.status_code == 200

    data = response.json()
    assert data["repository_id"] == repo.id
    assert data["repository_name"] == "api-repo"
    assert "health_score" in data
    assert "grade" in data
    assert "summary" in data


def test_get_repository_health_not_found(client, db_session):
    create_user(
        db=db_session,
        github_id=44444,
        username="healthuser",
        name="Health User",
        avatar_url="https://avatar.url",
        access_token="health_token",
    )
    response = client.get("/repositories/999999/health")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
