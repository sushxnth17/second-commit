from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RevivalTeam(Base):
    __tablename__ = "revival_teams"

    id: Mapped[int] = mapped_column(primary_key=True)

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    repository = relationship("Repository", back_populates="revival_team")
    owner = relationship("User", back_populates="owned_revival_teams")
    members = relationship(
        "RevivalTeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    work_items = relationship(
        "RevivalWorkItem",
        back_populates="team",
        cascade="all, delete-orphan",
    )
