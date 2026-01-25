from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
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
