from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from app.core.github_oauth import oauth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github")
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback", name="github_callback")
async def github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)

    response = await oauth.github.get(
        "user",
        token=token
    )

    profile = response.json()

    return {
        "login": profile["login"],
        "name": profile["name"],
        "id": profile["id"],
        "avatar_url": profile["avatar_url"],
        "html_url": profile["html_url"],
    }