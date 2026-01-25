"""Project service for project management operations."""

from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound, UnauthorizedAccess
from app.projects.models import Project
from app.projects.query import NotFoundProjectExc, ProjectQuery
from app.projects.schema import ProjectCreate, ProjectResponse, ProjectUpdate
from app.models import StatusMessage


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: Session):
        self.__query = ProjectQuery(db)

    def list_projects(self, user_id: int) -> list[ProjectResponse]:
        """
        Get list of all projects for a user.

        Args:
            user_id: ID of user

        Returns:
            List of ProjectResponse objects
        """
        projects = self.__query.list_projects(user_id)
        return [ProjectResponse.model_validate(project) for project in projects]

    def get_project(self, project_id: int, user_id: int) -> ProjectResponse:
        """
        Get a single project by ID.

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
            project = self.__query._get_project(project_id)
            self._check_ownership(project, user_id)
            return ProjectResponse.model_validate(project)
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
