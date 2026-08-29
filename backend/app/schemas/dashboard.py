from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field
from app.services.health_service import calculate_health_score
from app.services.dormancy_service import calculate_dormancy


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
    stars: int | None = None
    forks: int | None = None
    watchers: int | None = None
    open_issues: int | None = None
    size: int | None = None
    description: str | None = None
    pushed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published: bool = False

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def health_score(self) -> int:
        score, _, _ = calculate_health_score(self)
        return score

    @computed_field
    @property
    def health_grade(self) -> str:
        _, grade, _ = calculate_health_score(self)
        return grade

    @computed_field
    @property
    def dormancy_status(self) -> str:
        _, status, _ = calculate_dormancy(self)
        return status



class DashboardResponse(BaseModel):
    user: UserSummary
    repositories: list[RepositorySummary]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def total_repositories(self) -> int:
        return len(self.repositories)