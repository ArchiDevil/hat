from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.documents.models import doc_to_tm_link

if TYPE_CHECKING:
    from app.documents.models import Document
    from app.schema import User


class TranslationMemory(Base):
    __tablename__ = "translation_memory"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))

    records: Mapped[list["TranslationMemoryRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="TranslationMemoryRecord.id",
    )
    user: Mapped["User"] = relationship(back_populates="tms")
    docs: Mapped[list["Document"]] = relationship(
        secondary=doc_to_tm_link, back_populates="tms", order_by="Document.id"
    )


class TranslationMemoryRecord(Base):
    __tablename__ = "translation_memory_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("translation_memory.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()
    creation_date: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    change_date: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    document: Mapped["TranslationMemory"] = relationship(back_populates="records")


Index(
    "trgm_tm_src_idx",
    TranslationMemoryRecord.source,
    postgresql_using="gist",
    postgresql_ops={"source": "gist_trgm_ops"},
)
