from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.documents.models import Document, DocGlossaryAssociation

if TYPE_CHECKING:
    from app.schema import User


class ProcessingStatuses:
    IN_PROCESS = "IN_PROCESS"
    DONE = "DONE"


class Glossary(Base):
    __tablename__ = "glossary"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    name: Mapped[str] = mapped_column()
    processing_status: Mapped[str] = mapped_column(
        default=ProcessingStatuses.IN_PROCESS
    )
    upload_time: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))

    records: Mapped[list["GlossaryRecord"]] = relationship(
        back_populates="glossary",
        cascade="all, delete-orphan",
        order_by="GlossaryRecord.id",
    )
    user: Mapped["User"] = relationship(back_populates="glossaries")

    document_associations: Mapped[list["DocGlossaryAssociation"]] = relationship(
        back_populates="glossary", cascade="all, delete-orphan"
    )
    documents: AssociationProxy[list["Document"]] = association_proxy(
        "glossary_associations",
        "document",
        creator=lambda document: DocGlossaryAssociation(document=document),
    )


class GlossaryRecord(Base):
    __tablename__ = "glossary_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    comment: Mapped[str] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))

    glossary_id: Mapped[int] = mapped_column(ForeignKey("glossary.id"))
    glossary: Mapped["Glossary"] = relationship(back_populates="records")
    user: Mapped["User"] = relationship()

    stemmed_source: Mapped[str] = mapped_column()
