from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models import User
    from app.schema import TmxDocument, XliffDocument


doc_to_tmx_link = Table(
    "doc_to_tmx",
    Base.metadata,
    Column("doc_id", ForeignKey("document.id"), nullable=False),
    Column("tmx_id", ForeignKey("tmx_document.id"), nullable=False),
)


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    processing_status: Mapped[str] = mapped_column()
    upload_time: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    records: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentRecord.id",
    )
    user: Mapped["User"] = relationship("User", back_populates="documents")
    tmxs: Mapped[list["TmxDocument"]] = relationship(
        secondary=doc_to_tmx_link, back_populates="docs", order_by="TmxDocument.id"
    )
    xliff: Mapped["XliffDocument"] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )


class DocumentRecord(Base):
    __tablename__ = "document_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()

    document: Mapped["Document"] = relationship(back_populates="records")
