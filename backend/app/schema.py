from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class TmxDocument(Base):
    __tablename__ = "tmx_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    records: Mapped[list["TmxRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class TmxRecord(Base):
    __tablename__ = "tmx_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("tmx_document.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()

    document: Mapped["TmxDocument"] = relationship(back_populates="records")


class XliffDocument(Base):
    __tablename__ = "xliff_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    original_document: Mapped[str] = mapped_column()

    records: Mapped[list["XliffRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class XliffRecord(Base):
    __tablename__ = "xliff_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("xliff_document.id"))
    source: Mapped[str] = mapped_column()
    target: Mapped[str] = mapped_column()

    document: Mapped["XliffDocument"] = relationship(back_populates="records")
