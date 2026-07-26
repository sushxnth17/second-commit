from pydantic import BaseModel, ConfigDict, computed_field


class UserSummary(BaseModel):
    github_id: int
    username: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class RepositorySummary(BaseModel):
    id: int
    name: str
    language: str | None
    default_branch: str

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    user: UserSummary
    repositories: list[RepositorySummary]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def total_repositories(self) -> int:
        return len(self.repositories)