from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import create_user


def test_github_login(client, mocker):
    mock_authorize = mocker.patch(
        "app.core.github_oauth.oauth.github.authorize_redirect",
        return_value={"redirect_url": "https://github.com/login/oauth/authorize"}
    )
    
    response = client.get("/auth/github")
    assert response.status_code == 200
    assert response.json() == {"redirect_url": "https://github.com/login/oauth/authorize"}
    mock_authorize.assert_called_once()


def test_github_callback_existing_user(client, db_session, mocker):
    existing_user = create_user(
        db=db_session,
        github_id=12345,
        username="existinguser",
        name="Existing User",
        avatar_url="https://avatar.url",
        access_token="old_token",
    )

    mock_token = {"access_token": "new_token"}
    mock_profile = {
        "id": 12345,
        "login": "existinguser",
        "name": "Existing User Updated",
        "avatar_url": "https://avatar.url/updated",
    }

    mocker.patch(
        "app.core.github_oauth.oauth.github.authorize_access_token",
        new_callable=AsyncMock,
        return_value=mock_token
    )
    mock_response = MagicMock()
    mock_response.json.return_value = mock_profile
    mocker.patch(
        "app.core.github_oauth.oauth.github.get",
        new_callable=AsyncMock,
        return_value=mock_response
    )

    response = client.get("/auth/github/callback", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/dashboard"


def test_github_callback_new_user(client, db_session, mocker):
    mock_token = {"access_token": "new_token"}
    mock_profile = {
        "id": 67890,
        "login": "newuser",
        "name": "New User",
        "avatar_url": "https://avatar.url/new",
    }

    mocker.patch(
        "app.core.github_oauth.oauth.github.authorize_access_token",
        new_callable=AsyncMock,
        return_value=mock_token
    )
    mock_response = MagicMock()
    mock_response.json.return_value = mock_profile
    mocker.patch(
        "app.core.github_oauth.oauth.github.get",
        new_callable=AsyncMock,
        return_value=mock_response
    )

    response = client.get("/auth/github/callback", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/dashboard"


def test_logout_clears_session_and_rejects_subsequent_requests(client, db_session, mocker):
    from app.core.dependencies import get_current_user
    from app.main import app

    # Remove get_current_user dependency override so we test the real session verification
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    try:
        # 1. Log in by mocking callback
        mock_token = {"access_token": "test_logout_token"}
        mock_profile = {
            "id": 99999,
            "login": "logoutuser",
            "name": "Logout User",
            "avatar_url": "https://avatar.url",
        }
        mocker.patch(
            "app.core.github_oauth.oauth.github.authorize_access_token",
            new_callable=AsyncMock,
            return_value=mock_token
        )
        mock_response = MagicMock()
        mock_response.json.return_value = mock_profile
        mocker.patch(
            "app.core.github_oauth.oauth.github.get",
            new_callable=AsyncMock,
            return_value=mock_response
        )

        login_res = client.get("/auth/github/callback", follow_redirects=False)
        assert login_res.status_code == 307

        # Verify authenticated request works now
        auth_res = client.get("/repositories")
        assert auth_res.status_code == 200

        # 2. Call logout
        logout_res = client.post("/auth/logout")
        assert logout_res.status_code == 200
        assert logout_res.json() == {"message": "Logged out successfully"}

        # 3. Subsequent request should fail with 401
        post_logout_res = client.get("/repositories")
        assert post_logout_res.status_code == 401
        assert post_logout_res.json()["detail"] == "Not authenticated"
    finally:
        pass

