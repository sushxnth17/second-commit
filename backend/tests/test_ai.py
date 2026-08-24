from app.services.user_service import create_user
from app.services.repository_service import create_repository


def test_get_repository_ai_insights_success(client, db_session, mocker):
    # 1. Mock Groq Completions Create call
    mock_choices = mocker.MagicMock()
    mock_choices[0].message.content = (
        '{\n'
        '  "repository_name": "ai-test-repo",\n'
        '  "summary": "This is a great test repository with high quality code.",\n'
        '  "strengths": ["Well structured", "Good test coverage"],\n'
        '  "weaknesses": ["Lack of documentation", "Stale issues"],\n'
        '  "suggestions": ["Add a README", "Close old issues"],\n'
        '  "beginner_friendly": true,\n'
        '  "complexity": "Low",\n'
        '  "ai_score": 88.5\n'
        '}'
    )

    mock_completions = mocker.MagicMock()
    mock_completions.create = mocker.AsyncMock(return_value=mocker.MagicMock(choices=mock_choices))

    mock_client = mocker.MagicMock()
    mock_client.chat.completions = mock_completions

    mocker.patch("app.services.ai_service.AsyncGroq", return_value=mock_client)

    # 2. Create a test user and repository
    user = create_user(
        db=db_session,
        github_id=66666,
        username="aitester",
        name="AI Tester",
        avatar_url="https://avatar.url",
        access_token="ai_token",
    )

    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 601,
            "name": "ai-test-repo",
            "full_name": "aitester/ai-test-repo",
            "html_url": "https://github.com/aitester/ai-test-repo",
            "default_branch": "main",
        },
    )

    # 3. Call endpoint
    response = client.get(f"/repositories/{repo.id}/ai-insights")
    assert response.status_code == 200

    data = response.json()
    assert data["repository_name"] == "ai-test-repo"
    assert data["summary"] == "This is a great test repository with high quality code."
    assert data["strengths"] == ["Well structured", "Good test coverage"]
    assert data["beginner_friendly"] is True
    assert data["complexity"] == "Low"
    assert data["ai_score"] == 88.5


def test_get_repository_ai_insights_not_found(client, db_session):
    create_user(
        db=db_session,
        github_id=66666,
        username="aitester",
        name="AI Tester",
        avatar_url="https://avatar.url",
        access_token="ai_token",
    )
    response = client.get("/repositories/999999/ai-insights")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_get_repository_ai_insights_provider_error(client, db_session, mocker):
    # Mock Groq to raise an exception
    mocker.patch("app.services.ai_service.AsyncGroq", side_effect=Exception("Groq rate limit"))

    user = create_user(
        db=db_session,
        github_id=66667,
        username="aitester2",
        name="AI Tester 2",
        avatar_url="https://avatar.url",
        access_token="ai_token2",
    )

    repo = create_repository(
        db=db_session,
        owner_id=user.id,
        repo={
            "id": 602,
            "name": "ai-test-repo-2",
            "full_name": "aitester2/ai-test-repo-2",
            "html_url": "https://github.com/aitester2/ai-test-repo-2",
            "default_branch": "main",
        },
    )

    response = client.get(f"/repositories/{repo.id}/ai-insights")
    assert response.status_code == 502
    assert "AI service call failed" in response.json()["detail"]
