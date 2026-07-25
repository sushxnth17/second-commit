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
    response = client.get(f"/repositories/{user.github_id}")

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


def test_get_repositories_endpoint_user_not_found(client):
    # Call the API with a non-existent github_id
    response = client.get("/repositories/9999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
