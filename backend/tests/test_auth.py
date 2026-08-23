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
