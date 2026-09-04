from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RevivalWorkItemAssigneeSummary(BaseModel):
    id: int
    username: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RevivalWorkItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    assignee_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only")
        if len(trimmed) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return trimmed


class RevivalWorkItemResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    assignee: RevivalWorkItemAssigneeSummary | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevivalWorkItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str:
        if v is None:
            raise ValueError("Title cannot be null")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only")
        if len(trimmed) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return trimmed

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str:
        if v is None:
            raise ValueError("Status cannot be null")
        allowed = {"todo", "in_progress", "completed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v
