from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RevivalRoadmapTaskCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    position: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only")
        if len(trimmed) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return trimmed


class RevivalRoadmapTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None
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

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: int | None) -> int:
        if v is None:
            raise ValueError("Position cannot be null")
        return v


class RevivalRoadmapTaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    position: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevivalRoadmapPhaseCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    position: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or whitespace only")
        if len(trimmed) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return trimmed


class RevivalRoadmapPhaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None

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

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: int | None) -> int:
        if v is None:
            raise ValueError("Position cannot be null")
        return v


class RevivalRoadmapPhaseResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    position: int
    tasks: list[RevivalRoadmapTaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevivalRoadmapResponse(BaseModel):
    phases: list[RevivalRoadmapPhaseResponse] = []

    model_config = ConfigDict(from_attributes=True)
