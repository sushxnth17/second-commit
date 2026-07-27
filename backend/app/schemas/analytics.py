from pydantic import BaseModel, ConfigDict


class AnalyticsResponse(BaseModel):
    github_id: int
    total_repositories: int
    total_stars: int
    total_forks: int
    active_repositories: int
    dormant_repositories: int
    average_health_score: float
    primary_language: str | None = None
    most_popular_repository: str | None = None
    most_active_repository: str | None = None

    model_config = ConfigDict(from_attributes=True)
