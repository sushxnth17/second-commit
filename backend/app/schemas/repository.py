from datetime import datetime
from pydantic import BaseModel, ConfigDict


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


class RepositoryResponse(RepositoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)