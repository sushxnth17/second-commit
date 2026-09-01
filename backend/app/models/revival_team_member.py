from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RevivalTeamMember(Base):
    __tablename__ = "revival_team_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("revival_teams.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    team = relationship("RevivalTeam", back_populates="members")
    user = relationship("User", back_populates="revival_team_memberships")

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_revival_team_members_team_user",
        ),
    )
