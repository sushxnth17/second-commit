from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


ALLOWED_REVIVAL_STATUSES = {
    "seeking_revival",
    "forming_team",
    "revival_in_progress",
    "revived",
    "paused",
    "archived",
}


class RevivalStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ALLOWED_REVIVAL_STATUSES:
            raise ValueError(
                f"Status must be one of: {', '.join(sorted(ALLOWED_REVIVAL_STATUSES))}"
            )
        return v


class RepositoryBase(BaseModel):
    github_repo_id: int
    name: str
    full_name: str
    description: str | None = None
    language: str | None = None
    default_branch: str
    html_url: str
    stars: int | None = None
    forks: int | None = None
    watchers: int | None = None
    open_issues: int | None = None
    size: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    pushed_at: datetime | None = None
    published: bool = False
    revival_status: str = "seeking_revival"


class OwnerSummary(BaseModel):
    username: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RepositoryResponse(RepositoryBase):
    id: int
    owner_id: int | None = None
    owner: OwnerSummary | None = None

    model_config = ConfigDict(from_attributes=True)