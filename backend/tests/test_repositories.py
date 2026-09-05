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
        "owner_id",
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
        "published",
        "revival_status",
        "owner",
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
    assert repo_data["revival_status"] == "seeking_revival"


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
    assert "GitHub service is temporarily unavailable" in response.json()["detail"]


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


def test_import_repository_new(client, db_session, test_user, mocker):
    mock_repos = [
        {
            "id": 999,
            "name": "new-repo",
            "full_name": "testuser/new-repo",
            "description": "A new repo",
            "html_url": "https://github.com/testuser/new-repo",
            "language": "Python",
            "default_branch": "main",
            "stargazers_count": 0,
            "forks_count": 0,
            "watchers_count": 0,
            "open_issues_count": 0,
            "size": 100,
        }
    ]
    mocker.patch(
        "app.api.repositories.get_user_repositories",
        new_callable=mocker.AsyncMock,
        return_value=mock_repos
    )

    response = client.post("/repositories/import/999")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Repository imported successfully"
    assert data["repository"]["name"] == "new-repo"
    assert data["repository"]["id"] is not None


def test_import_repository_own_duplicate(client, db_session, test_user, mocker):
    from app.services.repository_service import create_repository
    repo_data = {
        "id": 999,
        "name": "new-repo",
        "full_name": "testuser/new-repo",
        "html_url": "https://github.com/testuser/new-repo",
        "default_branch": "main",
    }
    db_repo = create_repository(db_session, test_user.id, repo_data)

    mock_repos = [
        {
            "id": 999,
            "name": "new-repo",
            "full_name": "testuser/new-repo",
            "html_url": "https://github.com/testuser/new-repo",
            "default_branch": "main",
        }
    ]
    mocker.patch(
        "app.api.repositories.get_user_repositories",
        new_callable=mocker.AsyncMock,
        return_value=mock_repos
    )

    response = client.post("/repositories/import/999")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Repository already imported"
    assert data["repository"]["id"] == db_repo.id
    assert data["repository"]["name"] == "new-repo"


def test_import_repository_other_user_duplicate(client, db_session, test_user, auth_context, mocker):
    from app.services.user_service import create_user
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    from app.services.repository_service import create_repository
    repo_data = {
        "id": 999,
        "name": "new-repo",
        "full_name": "testuser/new-repo",
        "html_url": "https://github.com/testuser/new-repo",
        "default_branch": "main",
    }
    db_repo = create_repository(db_session, user_b.id, repo_data)

    auth_context.user = test_user

    mock_repos = [
        {
            "id": 999,
            "name": "new-repo",
            "full_name": "testuser/new-repo",
            "html_url": "https://github.com/testuser/new-repo",
            "default_branch": "main",
        }
    ]
    mocker.patch(
        "app.api.repositories.get_user_repositories",
        new_callable=mocker.AsyncMock,
        return_value=mock_repos
    )

    response = client.post("/repositories/import/999")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Repository is already associated with another account."
    assert "repository" not in data or data.get("repository") is None


def test_sync_repository_other_user(client, db_session, auth_context, mocker):
    from app.services.user_service import create_user
    user_a = create_user(
        db=db_session,
        github_id=11111,
        username="usera",
        name="User A",
        avatar_url="https://avatar.url",
        access_token="token_a",
    )
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    auth_context.user = user_a

    from app.services.repository_service import create_repository
    repo_b = create_repository(
        db=db_session,
        owner_id=user_b.id,
        repo={
            "id": 999,
            "name": "repo-b",
            "full_name": "userb/repo-b",
            "html_url": "https://github.com/userb/repo-b",
            "default_branch": "main",
        },
    )

    mock_get_details = mocker.patch("app.api.repositories.get_repository_details")

    response = client.post(f"/repositories/{repo_b.id}/sync")

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
    mock_get_details.assert_not_called()


def test_health_repository_other_user(client, db_session, auth_context, mocker):
    from app.services.user_service import create_user
    user_a = create_user(
        db=db_session,
        github_id=11111,
        username="usera",
        name="User A",
        avatar_url="https://avatar.url",
        access_token="token_a",
    )
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    auth_context.user = user_a

    from app.services.repository_service import create_repository
    repo_b = create_repository(
        db=db_session,
        owner_id=user_b.id,
        repo={
            "id": 999,
            "name": "repo-b",
            "full_name": "userb/repo-b",
            "html_url": "https://github.com/userb/repo-b",
            "default_branch": "main",
        },
    )

    mock_get_health = mocker.patch("app.api.health.get_health")

    response = client.get(f"/repositories/{repo_b.id}/health")

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
    mock_get_health.assert_not_called()


def test_dormancy_repository_other_user(client, db_session, auth_context, mocker):
    from app.services.user_service import create_user
    user_a = create_user(
        db=db_session,
        github_id=11111,
        username="usera",
        name="User A",
        avatar_url="https://avatar.url",
        access_token="token_a",
    )
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    auth_context.user = user_a

    from app.services.repository_service import create_repository
    repo_b = create_repository(
        db=db_session,
        owner_id=user_b.id,
        repo={
            "id": 999,
            "name": "repo-b",
            "full_name": "userb/repo-b",
            "html_url": "https://github.com/userb/repo-b",
            "default_branch": "main",
        },
    )

    mock_get_dormancy = mocker.patch("app.api.dormancy.get_repository_dormancy")

    response = client.get(f"/repositories/{repo_b.id}/dormancy")

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
    mock_get_dormancy.assert_not_called()


def test_ai_insights_repository_other_user(client, db_session, auth_context, mocker):
    from app.services.user_service import create_user
    user_a = create_user(
        db=db_session,
        github_id=11111,
        username="usera",
        name="User A",
        avatar_url="https://avatar.url",
        access_token="token_a",
    )
    user_b = create_user(
        db=db_session,
        github_id=22222,
        username="userb",
        name="User B",
        avatar_url="https://avatar.url",
        access_token="token_b",
    )

    auth_context.user = user_a

    from app.services.repository_service import create_repository
    repo_b = create_repository(
        db=db_session,
        owner_id=user_b.id,
        repo={
            "id": 999,
            "name": "repo-b",
            "full_name": "userb/repo-b",
            "html_url": "https://github.com/userb/repo-b",
            "default_branch": "main",
        },
    )

    mock_get_ai = mocker.patch("app.api.ai.get_ai_insights")

    response = client.get(f"/repositories/{repo_b.id}/ai-insights")

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
    mock_get_ai.assert_not_called()


def test_sync_repository_error_sanitization(client, db_session, test_user, mocker):
    from app.services.repository_service import create_repository
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 888,
            "name": "my-repo",
            "full_name": "testuser/my-repo",
            "html_url": "https://github.com/testuser/my-repo",
            "default_branch": "main",
        },
    )

    import httpx
    request = httpx.Request("GET", "https://api.github.com/repos/testuser/my-repo")
    fake_body = "secret_token=SHOULD_NOT_LEAK"
    response_obj = httpx.Response(status_code=502, request=request, text=fake_body)
    
    mocker.patch(
        "app.api.repositories.get_repository_details",
        new_callable=mocker.AsyncMock,
        side_effect=httpx.HTTPStatusError(
            message="Bad Gateway",
            request=request,
            response=response_obj
        )
    )

    response = client.post(f"/repositories/{repo.id}/sync")

    assert response.status_code == 502
    data = response.json()
    assert data["detail"] == "GitHub service is temporarily unavailable. Please try again later."
    assert "secret_token" not in response.text
    assert "SHOULD_NOT_LEAK" not in response.text


def test_repository_starts_unpublished(db_session, test_repo):
    # The default state should be False (unpublished)
    assert test_repo.published is False


def test_owner_can_publish_unpublish_repository(client, db_session, test_user, test_repo):
    # 1. Publish repository
    response = client.post(f"/repositories/{test_repo.id}/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_repo.id
    assert data["published"] is True

    # Check database status
    db_session.refresh(test_repo)
    assert test_repo.published is True

    # 2. Unpublish repository
    response = client.post(f"/repositories/{test_repo.id}/unpublish")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_repo.id
    assert data["published"] is False

    # Check database status
    db_session.refresh(test_repo)
    assert test_repo.published is False


def test_other_user_cannot_publish_unpublish_repository(client, db_session, test_repo, auth_context):
    from app.services.user_service import create_user
    # Create another user
    other_user = create_user(
        db=db_session,
        github_id=67890,
        username="otheruser",
        name="Other User",
        avatar_url="https://avatar.url/other",
        access_token="other_token",
    )

    # Set auth context to other_user
    auth_context.user = other_user

    # Try publishing owner's repository
    response = client.post(f"/repositories/{test_repo.id}/publish")
    assert response.status_code == 403
    assert response.json()["detail"] == "Repository owned by another user"

    # Try unpublishing owner's repository
    response = client.post(f"/repositories/{test_repo.id}/unpublish")
    assert response.status_code == 403
    assert response.json()["detail"] == "Repository owned by another user"


def test_unauthenticated_user_cannot_publish_unpublish_repository(client, test_repo, auth_context):
    # Set auth context to None (explicitly unauthenticated)
    auth_context.user = None

    response = client.post(f"/repositories/{test_repo.id}/publish")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    response = client.post(f"/repositories/{test_repo.id}/unpublish")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_publication_endpoint_not_found(client, db_session, test_user):
    # Repository does not exist
    response = client.post("/repositories/99999/publish")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"

    response = client.post("/repositories/99999/unpublish")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_discover_repositories(client, db_session, test_user):
    from app.services.repository_service import create_repository
    # Create two repositories: one published, one unpublished
    repo_published = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 301,
            "name": "repo-published",
            "full_name": "testuser/repo-published",
            "description": "This is published",
            "html_url": "https://github.com/testuser/repo-published",
            "language": "Python",
            "default_branch": "main",
        },
    )
    repo_published.published = True
    db_session.commit()

    repo_unpublished = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 302,
            "name": "repo-unpublished",
            "full_name": "testuser/repo-unpublished",
            "description": "This is unpublished",
            "html_url": "https://github.com/testuser/repo-unpublished",
            "language": "Python",
            "default_branch": "main",
        },
    )

    # Call discover endpoint
    response = client.get("/repositories/discover")
    assert response.status_code == 200
    data = response.json()

    # Assertions
    assert len(data) == 1
    assert data[0]["id"] == repo_published.id
    assert data[0]["published"] is True
    assert data[0]["owner"]["username"] == test_user.username
    assert data[0]["owner"]["avatar_url"] == test_user.avatar_url


def test_discover_repositories_ordering(client, db_session, test_user):
    from app.services.repository_service import create_repository
    # Create multiple published repositories
    repo1 = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 401,
            "name": "repo-first",
            "full_name": "testuser/repo-first",
            "html_url": "https://github.com/testuser/repo-first",
            "default_branch": "main",
        },
    )
    repo1.published = True

    repo2 = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 402,
            "name": "repo-second",
            "full_name": "testuser/repo-second",
            "html_url": "https://github.com/testuser/repo-second",
            "default_branch": "main",
        },
    )
    repo2.published = True
    db_session.commit()

    # Call discover
    response = client.get("/repositories/discover")
    assert response.status_code == 200
    data = response.json()

    # Assertions: sorted by ID desc (newest first, repo2 then repo1)
    assert len(data) == 2
    assert data[0]["id"] == repo2.id
    assert data[1]["id"] == repo1.id


def test_discover_repositories_unauthenticated(client, auth_context):
    # Set auth context to None (explicitly unauthenticated)
    auth_context.user = None

    response = client.get("/repositories/discover")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
