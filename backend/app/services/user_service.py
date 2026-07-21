from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_github_id(db: Session, github_id: int):
    return db.query(User).filter(User.github_id == github_id).first()


def create_user(
    db: Session,
    github_id: int,
    username: str,
    name: str | None,
    avatar_url: str | None,
):
    user = User(
        github_id=github_id,
        username=username,
        name=name,
        avatar_url=avatar_url,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user: User,
    username: str,
    name: str | None,
    avatar_url: str | None,
):
    user.username = username
    user.name = name
    user.avatar_url = avatar_url

    db.commit()
    db.refresh(user)

    return user