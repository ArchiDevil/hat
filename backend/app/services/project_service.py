"""Project service for project management operations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.documents.schema import DocumentWithRecordsCount
from app.models import DocumentStatus, StatusMessage
from app.projects.models import Project
from app.projects.query import NotFoundProjectExc, ProjectQuery
from app.projects.schema import (
    DetailedProjectResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: Session):
        self.__query = ProjectQuery(db)

    def list_projects(self, user_id: int) -> list[ProjectResponse]:
        """
        Get list of all projects for a user with aggregate metrics.

        Args:
            user_id: ID of user

        Returns:
            List of ProjectResponse objects
        """
        projects = self.__query.list_projects(user_id)
        return [
            ProjectResponse(
                id=-1,
                name="Unnamed project",
                created_by=-1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        ] + [
            ProjectResponse(
                id=project.id,
                name=project.name,
                created_by=project.created_by,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            for project in projects
        ]

    def get_project(self, project_id: int, user_id: int) -> DetailedProjectResponse:
        """
        Get a single project by ID with aggregate metrics.

        Args:
            project_id: Project ID
            user_id: ID of user requesting the project

        Returns:
            ProjectResponse object

        Raises:
            EntityNotFound: If project not found
            UnauthorizedAccess: If user doesn't own the project
        """
        try:
            project = (
                self.__query._get_project(project_id)
                if project_id != -1
                else Project(
                    id=-1,
                    name="Unnamed project",
                    created_by=-1,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            self._check_ownership(project, user_id)
            aggregates = self.__query.get_project_aggregates(
                project_id if project_id != -1 else None
            )
            documents = self.__query.get_project_documents(
                project_id if project_id != -1 else None
            )

            def find_doc(doc_id: int):
                for aggregate in aggregates:
                    if aggregate[0] == doc_id:
                        return aggregate
                return (0, 0, 0, 0, 0)

            return DetailedProjectResponse(
                id=project.id,
                name=project.name,
                created_by=project.created_by,
                created_at=project.created_at,
                updated_at=project.updated_at,
                documents=[
                    DocumentWithRecordsCount(
                        id=document.id,
                        name=document.name,
                        created_by=document.created_by,
                        status=DocumentStatus(document.processing_status),
                        type=document.type.value,
                        project_id=project.id,
                        approved_records_count=find_doc(document.id)[1],
                        total_records_count=find_doc(document.id)[2],
                        approved_word_count=find_doc(document.id)[3],
                        total_word_count=find_doc(document.id)[4],
                    )
                    for document in documents
                ],
                approved_records_count=sum([val[1] for val in aggregates]),
                total_records_count=sum([val[2] for val in aggregates]),
                approved_words_count=sum([val[3] for val in aggregates]),
                total_words_count=sum([val[4] for val in aggregates]),
            )
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

    def create_project(self, data: ProjectCreate, user_id: int) -> ProjectResponse:
        """
        Create a new project.

        Args:
            data: Project schema data
            user_id: ID of user creating the project

        Returns:
            Created ProjectResponse object
        """
        project = self.__query.create_project(user_id, data)
        return ProjectResponse.model_validate(project)

    def update_project(
        self, project_id: int, data: ProjectUpdate, user_id: int
    ) -> ProjectResponse:
        """
        Update a project.

        Args:
            project_id: Project ID
            data: Updated project schema data
            user_id: ID of user updating the project

        Returns:
            Updated ProjectResponse object

        Raises:
            EntityNotFound: If project not found
            UnauthorizedAccess: If user doesn't own the project
        """
        try:
            project = self.__query._get_project(project_id)
            self._check_ownership(project, user_id)
            updated_project = self.__query.update_project(project_id, data)
            return ProjectResponse.model_validate(updated_project)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

    def delete_project(self, project_id: int, user_id: int) -> StatusMessage:
        """
        Delete a project.

        Args:
            project_id: Project ID
            user_id: ID of user deleting the project

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If project not found
            UnauthorizedAccess: If user doesn't own the project
        """
        try:
            project = self.__query._get_project(project_id)
            self._check_ownership(project, user_id)
            if not self.__query.delete_project(project_id):
                raise EntityNotFound("Project", project_id)
            return StatusMessage(message="Deleted")
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

    def _check_ownership(self, project: Project, user_id: int) -> None:
        """
        Check if user owns the project.

        Args:
            project: Project object
            user_id: ID of user attempting the action

        Raises:
            UnauthorizedAccess: If user doesn't own the project
        """
        # Currently not implemented, left for the future
        pass
