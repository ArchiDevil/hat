from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.documents.models import DocMemoryAssociation, Document

if TYPE_CHECKING:
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

    document_associations: Mapped[list["DocMemoryAssociation"]] = relationship(
        back_populates="memory", cascade="all, delete-orphan"
    )
    document: AssociationProxy[list["Document"]] = association_proxy(
        "document_associations",
        "document",
        creator=lambda document: DocMemoryAssociation(document=document, mode="read"),
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
