import pytest
from app.services.github_service import get_user_repositories


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_user_repositories_single_page(mocker):
    # Mock Response objects: page 1 returns 10 items, page 2 returns empty
    mock_resp_1 = mocker.MagicMock()
    mock_resp_1.status_code = 200
    mock_resp_1.json.return_value = [{"id": i, "name": f"repo-{i}"} for i in range(10)]
    mock_resp_1.raise_for_status = mocker.MagicMock()

    mock_resp_2 = mocker.MagicMock()
    mock_resp_2.status_code = 200
    mock_resp_2.json.return_value = []
    mock_resp_2.raise_for_status = mocker.MagicMock()

    # Mock AsyncClient.get
    mock_get = mocker.AsyncMock(side_effect=[mock_resp_1, mock_resp_2])
    mocker.patch("httpx.AsyncClient.get", mock_get)

    repos = await get_user_repositories("test_token")

    assert len(repos) == 10
    assert repos[0]["name"] == "repo-0"

    # Assert get was called twice
    assert mock_get.call_count == 2

    # Assert get parameters for page 1
    mock_get.assert_any_call(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github+json",
        },
        params={"page": 1, "per_page": 100},
    )


@pytest.mark.anyio
async def test_get_user_repositories_multi_page(mocker):
    # Simulate page 1: 100 items, page 2: 15 items, page 3: empty
    page_1_repos = [{"id": i, "name": f"repo-{i}"} for i in range(100)]
    page_2_repos = [{"id": i, "name": f"repo-{i}"} for i in range(100, 115)]
    page_3_repos = []

    # Mock Response objects
    mock_resp_1 = mocker.MagicMock()
    mock_resp_1.status_code = 200
    mock_resp_1.json.return_value = page_1_repos
    mock_resp_1.raise_for_status = mocker.MagicMock()

    mock_resp_2 = mocker.MagicMock()
    mock_resp_2.status_code = 200
    mock_resp_2.json.return_value = page_2_repos
    mock_resp_2.raise_for_status = mocker.MagicMock()

    mock_resp_3 = mocker.MagicMock()
    mock_resp_3.status_code = 200
    mock_resp_3.json.return_value = page_3_repos
    mock_resp_3.raise_for_status = mocker.MagicMock()

    # AsyncClient.get side effect returning page_1, page_2, page_3 responses
    mock_get = mocker.AsyncMock(side_effect=[mock_resp_1, mock_resp_2, mock_resp_3])
    mocker.patch("httpx.AsyncClient.get", mock_get)

    repos = await get_user_repositories("test_token")

    # Assert exactly 115 unique repositories are returned
    assert len(repos) == 115
    assert repos[0]["name"] == "repo-0"
    assert repos[99]["name"] == "repo-99"
    assert repos[100]["name"] == "repo-100"
    assert repos[114]["name"] == "repo-114"

    # Assert it stopped after page 3 (3 calls)
    assert mock_get.call_count == 3

    # Assert page parameters are correct
    mock_get.assert_any_call(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github+json",
        },
        params={"page": 1, "per_page": 100},
    )
    mock_get.assert_any_call(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github+json",
        },
        params={"page": 2, "per_page": 100},
    )
    mock_get.assert_any_call(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": "Bearer test_token",
            "Accept": "application/vnd.github+json",
        },
        params={"page": 3, "per_page": 100},
    )
