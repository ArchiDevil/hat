from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.schema import User

if TYPE_CHECKING:
    from app.schema import User


class GlossaryDocument(Base):
    __tablename__ = "glossary_document"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    records: Mapped[list["GlossaryRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="GlossaryRecord.id",
    )
    user: Mapped["User"] = relationship(back_populates="glossaries")


class GlossaryRecord(Base):
    __tablename__ = "glossary_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    document_id: Mapped[int] = mapped_column(ForeignKey("glossary_document.id"))
    comment: Mapped[str] = mapped_column()
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()

    document: Mapped["GlossaryDocument"] = relationship(back_populates="records")
