from app.services.user_service import create_user
from app.services.repository_service import create_repository, get_repositories_by_owner


def test_get_repositories_by_owner(db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=12345,
        username="testuser",
        name="Test User",
        avatar_url="https://avatar.url",
        access_token="test_token",
    )

    # 2. Create repositories for the user
    repo1 = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 101,
            "name": "repo-one",
            "full_name": "testuser/repo-one",
            "description": "First repo description",
            "html_url": "https://github.com/testuser/repo-one",
            "language": "Python",
            "default_branch": "main",
        },
    )

    repo2 = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 102,
            "name": "repo-two",
            "full_name": "testuser/repo-two",
            "description": None,
            "html_url": "https://github.com/testuser/repo-two",
            "language": "JavaScript",
            "default_branch": "develop",
        },
    )

    # 3. Fetch repositories by owner
    repositories = get_repositories_by_owner(db_session, user.id)

    # 4. Assert correctness
    assert len(repositories) == 2
    assert repositories[0].id == repo1.id
    assert repositories[0].github_repo_id == 101
    assert repositories[0].name == "repo-one"
    assert repositories[1].id == repo2.id
    assert repositories[1].github_repo_id == 102
    assert repositories[1].name == "repo-two"


def test_get_repositories_endpoint(client, db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=54321,
        username="endpointuser",
        name="Endpoint User",
        avatar_url="https://avatar.url",
        access_token="token_endpoint",
    )

    # 2. Create repositories for the user
    create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 201,
            "name": "repo-alpha",
            "full_name": "endpointuser/repo-alpha",
            "description": "Alpha description",
            "html_url": "https://github.com/endpointuser/repo-alpha",
            "language": "Go",
            "default_branch": "main",
        },
    )

    # 3. Call the API endpoint
    response = client.get("/repositories")

    # 4. Assert responses
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    repo_data = data[0]
    # Check that it returns ONLY the requested keys
    expected_keys = {
        "id",
        "github_repo_id",
        "name",
        "full_name",
        "description",
        "language",
        "default_branch",
        "html_url",
        "stars",
        "forks",
        "watchers",
        "open_issues",
        "size",
        "created_at",
        "updated_at",
        "pushed_at",
    }
    assert set(repo_data.keys()) == expected_keys

    # Check content values
    assert repo_data["github_repo_id"] == 201
    assert repo_data["name"] == "repo-alpha"
    assert repo_data["full_name"] == "endpointuser/repo-alpha"
    assert repo_data["description"] == "Alpha description"
    assert repo_data["language"] == "Go"
    assert repo_data["default_branch"] == "main"
    assert repo_data["html_url"] == "https://github.com/endpointuser/repo-alpha"


def test_get_repositories_endpoint_unauthenticated(client):
    # Call the API without a user (unauthenticated)
    response = client.get("/repositories")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_sync_repository_success(client, db_session, mocker):
    from app.models.repository import Repository
    
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=98765,
        username="syncuser",
        name="Sync User",
        avatar_url="https://avatar.url",
        access_token="sync_token",
    )

    # 2. Create a repository for the user
    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 888,
            "name": "sync-repo",
            "full_name": "syncuser/sync-repo",
            "description": "Original description",
            "html_url": "https://github.com/syncuser/sync-repo",
            "language": "Python",
            "default_branch": "main",
        },
    )

    # 3. Mock GitHub API call in github_service
    mocker.patch(
        "app.api.repositories.get_repository_details",
        return_value={
            "id": 888,
            "name": "sync-repo-updated",
            "full_name": "syncuser/sync-repo-updated",
            "description": "Updated description",
            "html_url": "https://github.com/syncuser/sync-repo-updated",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 42,
            "forks_count": 7,
            "watchers_count": 12,
            "open_issues_count": 3,
            "size": 1500,
            "created_at": "2026-07-26T12:00:00Z",
            "updated_at": "2026-07-26T15:00:00Z",
            "pushed_at": "2026-07-26T16:00:00Z",
        }
    )

    # 4. Call sync endpoint
    response = client.post(f"/repositories/{repo.id}/sync")

    # 5. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == repo.id
    assert data["name"] == "sync-repo-updated"
    assert data["full_name"] == "syncuser/sync-repo-updated"
    assert data["description"] == "Updated description"
    assert data["stars"] == 42
    assert data["forks"] == 7
    assert data["watchers"] == 12
    assert data["open_issues"] == 3
    assert data["size"] == 1500
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    assert data["pushed_at"] is not None

    # Check that DB was also updated
    db_session.expire_all()
    db_repo = db_session.query(Repository).filter(Repository.id == repo.id).first()
    assert db_repo.name == "sync-repo-updated"
    assert db_repo.stars == 42


def test_sync_repository_not_found(client, db_session):
    create_user(
        db=db_session,
        github_id=98765,
        username="syncuser",
        name="Sync User",
        avatar_url="https://avatar.url",
        access_token="sync_token",
    )
    response = client.post("/repositories/99999/sync")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_sync_repository_github_failure(client, db_session, mocker):
    import httpx
    
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=98765,
        username="syncuser",
        name="Sync User",
        avatar_url="https://avatar.url",
        access_token="sync_token",
    )

    # 2. Create a repository for the user
    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 888,
            "name": "sync-repo",
            "full_name": "syncuser/sync-repo",
            "description": "Original description",
            "html_url": "https://github.com/syncuser/sync-repo",
            "language": "Python",
            "default_branch": "main",
        },
    )

    # 3. Mock get_repository_details to raise HTTPStatusError
    mock_response = httpx.Response(
        status_code=500,
        request=httpx.Request("GET", f"https://api.github.com/repos/{repo.full_name}")
    )
    mocker.patch(
        "app.api.repositories.get_repository_details",
        side_effect=httpx.HTTPStatusError("GitHub error", request=mock_response.request, response=mock_response)
    )

    # 4. Call sync endpoint
    response = client.post(f"/repositories/{repo.id}/sync")

    # 5. Assertions
    assert response.status_code == 502
    assert "GitHub API failure" in response.json()["detail"]


def test_get_repository_by_id_success(client, db_session):
    # 1. Create a test user
    user = create_user(
        db=db_session,
        github_id=123456,
        username="detailuser",
        name="Detail User",
        avatar_url="https://avatar.url",
        access_token="detail_token",
    )

    # 2. Create a repository
    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 777,
            "name": "detail-repo",
            "full_name": "detailuser/detail-repo",
            "description": "Detail repo description",
            "html_url": "https://github.com/detailuser/detail-repo",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 10,
            "forks_count": 2,
            "watchers_count": 5,
            "open_issues_count": 1,
            "size": 500,
        },
    )

    # 3. Call the API endpoint
    response = client.get(f"/repositories/{repo.id}")

    # 4. Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == repo.id
    assert data["github_repo_id"] == 777
    assert data["name"] == "detail-repo"
    assert data["full_name"] == "detailuser/detail-repo"
    assert data["description"] == "Detail repo description"
    assert data["language"] == "Python"
    assert data["default_branch"] == "main"
    assert data["html_url"] == "https://github.com/detailuser/detail-repo"
    assert data["stars"] == 10
    assert data["forks"] == 2
    assert data["watchers"] == 5
    assert data["open_issues"] == 1
    assert data["size"] == 500


def test_get_repository_by_id_not_found(client, db_session):
    # Create user so we are authenticated
    create_user(
        db=db_session,
        github_id=123456,
        username="detailuser",
        name="Detail User",
        avatar_url="https://avatar.url",
        access_token="detail_token",
    )
    response = client.get("/repositories/999999")
    assert response.status_code == 404


def test_get_repository_by_id_unauthenticated(client):
    response = client.get("/repositories/777")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_repository_by_id_other_user(client, db_session, auth_context):
    # 1. Create User A
    user_a = create_user(
        db=db_session,
        github_id=11111,
        username="usera",
        name="User A",
        avatar_url="https://avatar.url",
        access_token="token_a",
    )

    # 2. Create User B
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    # Explicitly authenticate as User A
    auth_context.user = user_a

    # 3. Create repository belonging to User B
    repo_b = create_repository(
        db=db_session,
        owner_id=user_b.id,
        repo={
            "id": 999,
            "name": "repo-b",
            "full_name": "userb/repo-b",
            "description": "User B repository",
            "html_url": "https://github.com/userb/repo-b",
            "language": "Python",
            "default_branch": "main",
        },
    )

    # 4. Request User B's repository as User A
    response = client.get(f"/repositories/{repo_b.id}")
    
    # 5. Assert HTTP 404 (ownership check failure returns 404)
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_service_create_repository(db_session, test_user):
    from app.services.repository_service import create_repository
    repo_data = {
        "id": 999,
        "name": "new-repo",
        "full_name": "testuser/new-repo",
        "description": "New repository",
        "html_url": "https://github.com/testuser/new-repo",
        "language": "Python",
        "default_branch": "main",
    }
    repo = create_repository(db_session, test_user.id, repo_data)
    assert repo.id is not None
    assert repo.github_repo_id == 999
    assert repo.name == "new-repo"
    assert repo.owner_id == test_user.id


def test_service_get_repository_by_github_id(db_session, test_repo):
    from app.services.repository_service import get_repository_by_github_id
    fetched = get_repository_by_github_id(db_session, test_repo.github_repo_id)
    assert fetched is not None
    assert fetched.id == test_repo.id


def test_service_get_repositories_by_owner(db_session, test_user, test_repo):
    from app.services.repository_service import get_repositories_by_owner
    fetched = get_repositories_by_owner(db_session, test_user.id)
    assert len(fetched) == 1
    assert fetched[0].id == test_repo.id


def test_service_get_repository_by_id(db_session, test_repo):
    from app.services.repository_service import get_repository_by_id
    fetched = get_repository_by_id(db_session, test_repo.id)
    assert fetched is not None
    assert fetched.id == test_repo.id


def test_service_get_repository_by_id_missing(db_session):
    import pytest
    from app.services.repository_service import get_repository_by_id
    with pytest.raises(ValueError) as exc_info:
        get_repository_by_id(db_session, 99999)
    assert str(exc_info.value) == "Repository not found"

