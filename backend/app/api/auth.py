from fastapi import APIRouter, Request

from app.core.github_oauth import oauth
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.user_service import (
    get_user_by_github_id,
    create_user,
    update_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github")
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback", name="github_callback")
async def github_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    token = await oauth.github.authorize_access_token(request)

    response = await oauth.github.get(
        "user",
        token=token
    )

    profile = response.json()

    user = get_user_by_github_id(db, profile["id"])

    if user is None:
        user = create_user(
            db=db,
            github_id=profile["id"],
            username=profile["login"],
            name=profile.get("name"),
            avatar_url=profile.get("avatar_url"),
        )
    else:
        user = update_user(
            db=db,
            user=user,
            username=profile["login"],
            name=profile.get("name"),
            avatar_url=profile.get("avatar_url"),
        )

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "github_id": user.github_id,
            "username": user.username,
            "name": user.name,
            "avatar_url": user.avatar_url,
    },
}