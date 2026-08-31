from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.dashboard import UserSummary


class RevivalRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=1000)


class RevivalRequestResponse(BaseModel):
    id: int
    repository_id: int
    requester_id: int
    message: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    requester: UserSummary | None = None

    model_config = ConfigDict(from_attributes=True)
