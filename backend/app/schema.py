from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.documents.models import doc_to_tmx_link

if TYPE_CHECKING:
    from app.documents.models import Document
    from app.glossary.models import GlossaryDocument


class TmxDocument(Base):
    __tablename__ = "tmx_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))

    records: Mapped[list["TmxRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="TmxRecord.id"
    )
    user: Mapped["User"] = relationship(back_populates="tmxs")
    docs: Mapped[list["Document"]] = relationship(
        secondary=doc_to_tmx_link, back_populates="tmxs", order_by="Document.id"
    )


class TmxRecord(Base):
    __tablename__ = "tmx_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("tmx_document.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()
    creation_date: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    change_date: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    document: Mapped["TmxDocument"] = relationship(back_populates="records")


Index(
    "trgm_tmx_src_idx",
    TmxRecord.source,
    postgresql_using="gist",
    postgresql_ops={"source": "gist_trgm_ops"},
)


class DocumentTask(Base):
    __tablename__ = "document_task"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[str] = mapped_column(default="user")
    disabled: Mapped[bool] = mapped_column(default=False)

    tmxs: Mapped[list["TmxDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="TmxDocument.id"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Document.id"
    )
    glossaries: Mapped[list["GlossaryDocument"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="GlossaryDocument.id",
    )
