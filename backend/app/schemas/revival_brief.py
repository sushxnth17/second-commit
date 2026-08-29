from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RevivalBriefBase(BaseModel):
    developer_notes: str = ""
    revival_intent: str = ""
    status: str = "draft"


class RevivalBriefCreate(RevivalBriefBase):
    pass


class RevivalBriefUpdate(BaseModel):
    developer_notes: str | None = None
    revival_intent: str | None = None
    status: str | None = None


class RevivalBriefResponse(RevivalBriefBase):
    id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
