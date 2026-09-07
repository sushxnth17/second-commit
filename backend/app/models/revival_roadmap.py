from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, String, Text, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RevivalRoadmapPhase(Base):
    __tablename__ = "revival_roadmap_phases"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("revival_teams.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
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

    team = relationship("RevivalTeam", back_populates="roadmap_phases")
    tasks = relationship(
        "RevivalRoadmapTask",
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="RevivalRoadmapTask.position.asc(), RevivalRoadmapTask.id.asc()",
    )


class RevivalRoadmapTask(Base):
    __tablename__ = "revival_roadmap_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    phase_id: Mapped[int] = mapped_column(
        ForeignKey("revival_roadmap_phases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="todo",
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

    phase = relationship("RevivalRoadmapPhase", back_populates="tasks")

    __table_args__ = (
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'completed')",
            name="ck_revival_roadmap_tasks_status",
        ),
    )
