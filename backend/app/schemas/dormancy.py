from pydantic import BaseModel, ConfigDict


class DormancyResponse(BaseModel):
    repository_id: int
    repository_name: str
    days_since_last_push: int | None = None
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)
