from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.documents.models import Document
    from app.glossary.models import Glossary
    from app.schema import User


def utc_time():
    return datetime.now(UTC)


class ProjectGlossaryAssociation(Base):
    __tablename__ = "project_glossary"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    glossary_id: Mapped[int] = mapped_column(ForeignKey("glossary.id"))

    project: Mapped["Project"] = relationship(back_populates="glossary_associations")
    glossary: Mapped["Glossary"] = relationship(back_populates="project_associations")
    PrimaryKeyConstraint(project_id, glossary_id)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(default=utc_time)
    updated_at: Mapped[datetime] = mapped_column(default=utc_time)

    user: Mapped["User"] = relationship(back_populates="projects")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    glossary_associations: Mapped[list["ProjectGlossaryAssociation"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    glossaries: AssociationProxy[list["Glossary"]] = association_proxy(
        "glossary_associations",
        "glossary",
        creator=lambda glossary: ProjectGlossaryAssociation(glossary=glossary),
    )
