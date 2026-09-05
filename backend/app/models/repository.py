from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)

    github_repo_id: Mapped[int] = mapped_column(unique=True, index=True)

    name: Mapped[str] = mapped_column(String(255))

    full_name: Mapped[str] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(nullable=True)

    html_url: Mapped[str] = mapped_column(String(500))

    language: Mapped[str | None] = mapped_column(String(100), nullable=True)

    default_branch: Mapped[str] = mapped_column(String(100))

    stars: Mapped[int | None] = mapped_column(nullable=True)

    forks: Mapped[int | None] = mapped_column(nullable=True)

    watchers: Mapped[int | None] = mapped_column(nullable=True)

    open_issues: Mapped[int | None] = mapped_column(nullable=True)

    size: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    published: Mapped[bool] = mapped_column(default=False)

    revival_status: Mapped[str] = mapped_column(
        String(50),
        default="seeking_revival",
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )

    owner = relationship("User")

    revival_brief = relationship(
        "RevivalBrief",
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )

    revival_team = relationship(
        "RevivalTeam",
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "revival_status IN ('seeking_revival', 'forming_team', 'revival_in_progress', 'revived', 'paused', 'archived')",
            name="ck_repositories_revival_status",
        ),
    )