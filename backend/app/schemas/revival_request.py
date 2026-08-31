from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.dashboard import UserSummary


class RevivalRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=1000)


class RequesterSummary(BaseModel):
    username: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RevivalRequestResponse(BaseModel):
    id: int
    repository_id: int
    requester_id: int
    message: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    requester: RequesterSummary | None = None

    model_config = ConfigDict(from_attributes=True)
