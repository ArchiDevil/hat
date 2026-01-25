from datetime import UTC, datetime

from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.documents.models import Document, DocumentRecord
from app.projects.models import Project
from app.projects.schema import ProjectCreate, ProjectUpdate


class NotFoundProjectExc(BaseQueryException):
    """Not found project"""


class ProjectQuery:
    """Contain query to Project"""

    def __init__(self, db: Session):
        self.__db = db

    def _get_project(self, project_id: int) -> Project:
        project = self.__db.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        if project:
            return project
        raise NotFoundProjectExc()

    def list_projects(self, user_id: int) -> list[Project]:
        """List all projects for a specific user."""
        return list(
            self.__db.execute(select(Project).order_by(Project.id)).scalars().all()
        )

    def create_project(self, user_id: int, data: ProjectCreate) -> Project:
        project = Project(user_id=user_id, name=data.name)
        self.__db.add(project)
        self.__db.commit()
        return project

    def update_project(self, project_id: int, data: ProjectUpdate) -> Project:
        dump = data.model_dump()
        dump["updated_at"] = datetime.now(UTC)
        self.__db.execute(update(Project).where(Project.id == project_id).values(dump))
        self.__db.commit()
        return self._get_project(project_id)

    def delete_project(self, project_id: int) -> bool:
        project = self.__db.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()
        if not project:
            return False

        self.__db.delete(project)
        self.__db.commit()
        return True

    def get_project_aggregates(self, project_id: int) -> tuple[int, int, int, int]:
        """
        Get aggregate metrics for a project.

        Returns a tuple containing:
        - approved_segments_count: Total approved segments across all documents
        - total_segments_count: Total segments across all documents
        - approved_words_count: Total approved words across all documents
        - total_words_count: Total words across all documents

        Args:
            project_id: ID of the project

        Returns:
            Tuple of four integers: (approved_segments_count, total_segments_count,
                                      approved_words_count, total_words_count)
        """
        stmt = (
            select(
                func.sum(case((DocumentRecord.approved.is_(True), 1), else_=0)).label(
                    "approved_segments"
                ),
                func.count(DocumentRecord.id).label("total_segments"),
                func.sum(
                    case(
                        (DocumentRecord.approved.is_(True), DocumentRecord.word_count),
                        else_=0,
                    )
                ).label("approved_words"),
                func.sum(DocumentRecord.word_count).label("total_words"),
            )
            .select_from(DocumentRecord)
            .join(Document, DocumentRecord.document_id == Document.id)
            .where(Document.project_id == project_id)
        )

        result = self.__db.execute(stmt).one()
        return (
            result.approved_segments or 0,
            result.total_segments or 0,
            result.approved_words or 0,
            result.total_words or 0,
        )
