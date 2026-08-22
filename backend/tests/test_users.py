from app.services.user_service import create_user, get_user_by_github_id, update_user


def test_create_user(db_session):
    user = create_user(
        db=db_session,
        github_id=98765,
        username="newuser",
        name="New User",
        avatar_url="https://avatar.url/new",
        access_token="new_token",
    )
    assert user.id is not None
    assert user.github_id == 98765
    assert user.username == "newuser"
    assert user.name == "New User"
    assert user.avatar_url == "https://avatar.url/new"
    assert user.access_token == "new_token"


def test_get_user_by_github_id(db_session, test_user):
    fetched = get_user_by_github_id(db_session, test_user.github_id)
    assert fetched is not None
    assert fetched.id == test_user.id


def test_update_user(db_session, test_user):
    updated = update_user(
        db=db_session,
        user=test_user,
        username="updateduser",
        name="Updated Name",
        avatar_url="https://avatar.url/updated",
        access_token="updated_token",
    )
    assert updated.id == test_user.id
    assert updated.username == "updateduser"
    assert updated.name == "Updated Name"
    assert updated.avatar_url == "https://avatar.url/updated"
    assert updated.access_token == "updated_token"
