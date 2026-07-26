from app.services.user_service import create_user
from app.services.repository_service import create_repository


def test_get_dashboard_success(client, db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=12345,
        username="dashboarduser",
        name="Dashboard User",
        avatar_url="https://avatar.url",
        access_token="token_dashboard",
    )

    # 2. Create repository for the user
    create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 501,
            "name": "repo-dashboard",
            "full_name": "dashboarduser/repo-dashboard",
            "description": "Dashboard repository",
            "html_url": "https://github.com/dashboarduser/repo-dashboard",
            "language": "Python",
            "default_branch": "main",
        },
    )

    # 3. Call the API endpoint
    response = client.get(f"/dashboard/{user.github_id}")

    # 4. Assert responses
    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "user" in data
    assert "repositories" in data
    assert "total_repositories" in data

    # Check user data
    user_data = data["user"]
    assert user_data["github_id"] == 12345
    assert user_data["username"] == "dashboarduser"
    assert user_data["name"] == "Dashboard User"

    # Check repositories data
    repos_data = data["repositories"]
    assert isinstance(repos_data, list)
    assert len(repos_data) == 1

    repo_data = repos_data[0]
    # Check expected keys
    expected_repo_keys = {"id", "name", "language", "default_branch"}
    assert set(repo_data.keys()) == expected_repo_keys
    assert repo_data["name"] == "repo-dashboard"
    assert repo_data["language"] == "Python"
    assert repo_data["default_branch"] == "main"

    # Check total
    assert data["total_repositories"] == 1


def test_get_dashboard_user_not_found(client):
    # Call the API with a non-existent github_id
    response = client.get("/dashboard/9999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
