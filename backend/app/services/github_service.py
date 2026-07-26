import httpx


async def get_user_repositories(access_token: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers=headers,
        )

    response.raise_for_status()

    return response.json()


async def get_repository_details(access_token: str, full_name: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{full_name}",
            headers=headers,
        )

    response.raise_for_status()

    return response.json()