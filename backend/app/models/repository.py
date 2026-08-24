from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
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

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )

    owner = relationship("User")