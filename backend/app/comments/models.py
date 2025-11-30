from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.documents.models import DocumentRecord
    from app.models import User


class Comment(Base):
    __tablename__ = "record_comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    record_id: Mapped[int] = mapped_column(ForeignKey("document_record.id"))

    created_by_user: Mapped["User"] = relationship("User", back_populates="comments")
    document_record: Mapped["DocumentRecord"] = relationship(back_populates="comments")
