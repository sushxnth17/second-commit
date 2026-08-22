from datetime import datetime, timezone, timedelta
from app.services.user_service import create_user
from app.services.repository_service import create_repository
from app.services.analytics_service import get_developer_analytics


def test_get_developer_analytics_success(client, db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=55555,
        username="analyticstester",
        name="Analytics Tester",
        avatar_url="https://avatar.url",
        access_token="analytics_token",
    )

    # 2. Create multiple repositories with varying stats
    # repo1: python, active, stars: 100, forks: 20
    create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 701,
            "name": "python-active-repo",
            "full_name": "analyticstester/python-active-repo",
            "description": "Python active description",
            "html_url": "https://github.com/analyticstester/python-active-repo",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 100,
            "forks_count": 20,
            "open_issues_count": 5,
            "size": 1000,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    )

    # repo2: python, dormant, stars: 50, forks: 10
    create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 702,
            "name": "python-dormant-repo",
            "full_name": "analyticstester/python-dormant-repo",
            "description": "Python dormant description",
            "html_url": "https://github.com/analyticstester/python-dormant-repo",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 50,
            "forks_count": 10,
            "open_issues_count": 2,
            "size": 500,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=300)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
        },
    )

    # repo3: javascript, slowing down, stars: 200, forks: 40
    create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 703,
            "name": "javascript-repo",
            "full_name": "analyticstester/javascript-repo",
            "description": "JavaScript description",
            "html_url": "https://github.com/analyticstester/javascript-repo",
            "language": "JavaScript",
            "default_branch": "main",
            "stargazers_count": 200,
            "forks_count": 40,
            "open_issues_count": 1,
            "size": 800,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
            "pushed_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
        },
    )

    # 3. Call endpoint
    response = client.get("/analytics")
    assert response.status_code == 200

    data = response.json()
    assert data["github_id"] == user.github_id
    assert data["total_repositories"] == 3
    assert data["total_stars"] == 350
    assert data["total_forks"] == 70
    assert data["active_repositories"] == 1
    assert data["dormant_repositories"] == 1
    assert data["primary_language"] == "Python"
    assert data["most_popular_repository"] == "javascript-repo"  # 200 stars
    assert data["most_active_repository"] == "python-active-repo"  # pushed 5 days ago (latest)
    assert "average_health_score" in data


def test_get_developer_analytics_unauthenticated(client):
    response = client.get("/analytics")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
