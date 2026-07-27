from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    repository_id: int
    repository_name: str
    health_score: int
    grade: str
    summary: str

    model_config = ConfigDict(from_attributes=True)
