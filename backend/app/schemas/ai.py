from pydantic import BaseModel, ConfigDict


class AIInsightsResponse(BaseModel):
    repository_name: str
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    beginner_friendly: bool
    complexity: str
    ai_score: float

    model_config = ConfigDict(from_attributes=True)
