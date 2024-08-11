from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.documents.models import Document
    from app.glossary.models import GlossaryDocument
    from app.translation_memory.models import TranslationMemory


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

    tms: Mapped[list["TranslationMemory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="TranslationMemory.id",
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Document.id"
    )
    glossaries: Mapped[list["GlossaryDocument"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="GlossaryDocument.id",
    )
