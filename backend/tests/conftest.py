import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.database import get_db
from app.main import app

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)



@pytest.fixture(name="db_session")
def fixture_db_session():
    # Import models to ensure they register on Base.metadata
    import app.models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class AuthContext:
    def __init__(self):
        self._user = None
        self.explicit = False

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, val):
        self._user = val
        self.explicit = True


@pytest.fixture(name="auth_context")
def fixture_auth_context():
    return AuthContext()


@pytest.fixture(name="client")
def fixture_client(db_session, auth_context):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        if auth_context.explicit:
            if auth_context.user is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Not authenticated")
            return auth_context.user

        # Fallback to the first user in the database for backward compatibility
        from app.models.user import User
        user = db_session.query(User).first()
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    from app.core.dependencies import get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def fixture_test_user(db_session):
    from app.services.user_service import create_user
    user = create_user(
        db=db_session,
        github_id=12345,
        username="testuser",
        name="Test User",
        avatar_url="https://avatar.url",
        access_token="test_token",
    )
    return user


@pytest.fixture(name="test_repo")
def fixture_test_repo(db_session, test_user):
    from app.services.repository_service import create_repository
    repo_data = {
        "id": 101,
        "name": "repo-one",
        "full_name": "testuser/repo-one",
        "description": "First repo description",
        "html_url": "https://github.com/testuser/repo-one",
        "language": "Python",
        "default_branch": "main",
        "stargazers_count": 5,
        "forks_count": 2,
        "watchers_count": 5,
        "open_issues_count": 1,
        "size": 100,
    }
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo=repo_data,
    )
    return repo
