from pydantic import BaseModel, ConfigDict


class RepositoryBase(BaseModel):
    github_repo_id: int
    name: str
    full_name: str
    description: str | None = None
    language: str | None = None
    default_branch: str
    html_url: str


class RepositoryResponse(RepositoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)