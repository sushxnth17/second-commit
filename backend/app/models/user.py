from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    github_id: Mapped[int] = mapped_column(unique=True, index=True)

    username: Mapped[str] = mapped_column(String(100))

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    avatar_url: Mapped[str | None] = mapped_column(
        nullable=True
    )
    access_token: Mapped[str | None] = mapped_column(
        nullable=True
    )
    
    repositories = relationship(
        "Repository",
        back_populates="owner",
    )