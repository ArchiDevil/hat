from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models import User


def utc_time():
    return datetime.now(UTC)


class RegistrationToken(Base):
    """Registration token for user sign-up."""

    __tablename__ = "registration_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_time)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))

    created_by_user: Mapped["User"] = relationship("User")
