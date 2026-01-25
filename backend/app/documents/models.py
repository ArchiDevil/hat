from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.comments.models import Comment
    from app.glossary.models import Glossary
    from app.models import User
    from app.projects.models import Project
    from app.translation_memory.models import TranslationMemory


def utc_time():
    return datetime.now(UTC)


class DocumentRecordHistoryChangeType(Enum):
    initial_import = "initial_import"
    machine_translation = "machine_translation"
    tm_substitution = "tm_substitution"
    glossary_substitution = "glossary_substitution"
    repetition = "repetition"
    manual_edit = "manual_edit"


class TmMode(Enum):
    read = "read"
    write = "write"


class DocMemoryAssociation(Base):
    __tablename__ = "document_to_translation_memory"

    doc_id: Mapped[int] = mapped_column(ForeignKey("document.id"), primary_key=True)
    tm_id: Mapped[int] = mapped_column(
        ForeignKey("translation_memory.id"), primary_key=True
    )
    mode: Mapped[TmMode] = mapped_column(type_=SqlEnum(TmMode), primary_key=True)

    document: Mapped["Document"] = relationship(back_populates="memory_associations")
    memory: Mapped["TranslationMemory"] = relationship(
        back_populates="document_associations"
    )
    PrimaryKeyConstraint(doc_id, tm_id, mode)


class DocGlossaryAssociation(Base):
    __tablename__ = "glossary_to_document"

    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    glossary_id: Mapped[int] = mapped_column(ForeignKey("glossary.id"))

    document: Mapped["Document"] = relationship(back_populates="glossary_associations")
    glossary: Mapped["Glossary"] = relationship(back_populates="document_associations")
    PrimaryKeyConstraint(document_id, glossary_id)


class DocumentType(Enum):
    xliff = "xliff"
    txt = "txt"


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    type: Mapped[DocumentType] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    processing_status: Mapped[str] = mapped_column()
    upload_time: Mapped[datetime] = mapped_column(default=utc_time)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True
    )

    records: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentRecord.id",
    )
    user: Mapped["User"] = relationship("User", back_populates="documents")
    project: Mapped["Project"] = relationship(back_populates="documents")
    xliff: Mapped["XliffDocument"] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    txt: Mapped["TxtDocument"] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )

    memory_associations: Mapped[list[DocMemoryAssociation]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    memories: AssociationProxy[list["TranslationMemory"]] = association_proxy(
        "memory_associations",
        "memory",
        creator=lambda memory: DocMemoryAssociation(memory=memory, mode="read"),
    )

    glossary_associations: Mapped[list[DocGlossaryAssociation]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    glossaries: AssociationProxy[list["Glossary"]] = association_proxy(
        "glossary_associations",
        "glossary",
        creator=lambda glossary: DocGlossaryAssociation(glossary=glossary),
    )


class DocumentRecord(Base):
    __tablename__ = "document_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()
    approved: Mapped[bool] = mapped_column(default=False)
    word_count: Mapped[int] = mapped_column(default=0)

    document: Mapped["Document"] = relationship(back_populates="records")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="document_record",
        cascade="all, delete-orphan",
        order_by="Comment.id",
    )
    history: Mapped[list["DocumentRecordHistory"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="DocumentRecordHistory.timestamp.desc()",
    )


class TxtDocument(Base):
    __tablename__ = "txt_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    original_document: Mapped[str] = mapped_column()

    records: Mapped[list["TxtRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="TxtRecord.id",
    )
    parent: Mapped["Document"] = relationship(back_populates="txt", single_parent=True)


class TxtRecord(Base):
    __tablename__ = "txt_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("document_record.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("txt_document.id"))
    offset: Mapped[int] = mapped_column()

    parent: Mapped["DocumentRecord"] = relationship()
    document: Mapped["TxtDocument"] = relationship(back_populates="records")


class XliffDocument(Base):
    __tablename__ = "xliff_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    original_document: Mapped[str] = mapped_column()

    records: Mapped[list["XliffRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="XliffRecord.id",
    )
    parent: Mapped["Document"] = relationship(
        back_populates="xliff", single_parent=True
    )


class XliffRecord(Base):
    __tablename__ = "xliff_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("document_record.id"))
    segment_id: Mapped[int] = mapped_column()
    document_id: Mapped[int] = mapped_column(ForeignKey("xliff_document.id"))
    state: Mapped[str] = mapped_column()

    parent: Mapped["DocumentRecord"] = relationship()
    document: Mapped["XliffDocument"] = relationship(back_populates="records")


class DocumentRecordHistory(Base):
    __tablename__ = "document_record_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("document_record.id"))
    diff: Mapped[str] = mapped_column()
    author_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(default=utc_time)
    change_type: Mapped[DocumentRecordHistoryChangeType] = mapped_column()

    record: Mapped["DocumentRecord"] = relationship(back_populates="history")
    author: Mapped["User"] = relationship()


Index("document_record_history_record_id_idx", DocumentRecordHistory.record_id)
