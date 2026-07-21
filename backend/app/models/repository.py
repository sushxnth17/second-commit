from sqlalchemy import String, ForeignKey
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

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    owner = relationship("User")