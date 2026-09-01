from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TeamUserSummary(BaseModel):
    id: int
    username: str
    name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RevivalTeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    joined_at: datetime
    user: TeamUserSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class RevivalTeamResponse(BaseModel):
    id: int
    repository_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: TeamUserSummary | None = None
    members: list[RevivalTeamMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)
