"""Project service for project management operations."""

from sqlalchemy.orm import Session

from app.base.exceptions import BusinessLogicError, EntityNotFound
from app.documents.models import TmMode
from app.documents.schema import DocumentWithRecordsCount
from app.glossary.query import GlossaryQuery, NotFoundGlossaryExc
from app.glossary.schema import GlossaryResponse
from app.models import DocumentStatus, StatusMessage
from app.projects.models import Project
from app.projects.query import NotFoundProjectExc, ProjectQuery
from app.projects.schema import (
    DetailedProjectResponse,
    ProjectCreate,
    ProjectGlossary,
    ProjectResponse,
    ProjectTm,
    ProjectTmUpdate,
    ProjectTranslationMemory,
    ProjectUpdate,
)
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import (
    TranslationMemory,
    TranslationMemoryListResponse,
    TranslationMemoryListSimilarResponse,
)


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: Session):
        self.__query = ProjectQuery(db)
        self.__glossary_query = GlossaryQuery(db)
        self.__tm_query = TranslationMemoryQuery(db)

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
            project = self.__query._get_project(project_id)
            self._check_ownership(project, user_id)
            aggregates = self.__query.get_project_aggregates(project_id)
            documents = self.__query.get_project_documents(project_id)

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

    def get_glossaries(self, project_id: int) -> ProjectGlossary:
        """
        Get glossaries for a project.

        Args:
            project_id: Project ID

        Returns:
            List of dictionaries with project_id and glossary

        Raises:
            EntityNotFound: If project not found
        """
        try:
            project = self.__query._get_project(project_id)
            return ProjectGlossary(
                id=project.id,
                glossaries=[
                    GlossaryResponse.model_validate(x.glossary)
                    for x in project.glossary_associations
                ],
            )

        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

    def set_glossaries(self, project_id: int, glossary_ids: list[int]) -> StatusMessage:
        """
        Set glossaries for a project.

        Args:
            project_id: Project ID
            glossary_ids: List of glossary IDs to associate with the project

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If project or glossaries not found
        """
        try:
            project = self.__query._get_project(project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

        if not glossary_ids:
            glossaries = []
        else:
            try:
                glossaries = self.__glossary_query.get_glossaries(glossary_ids)
            except NotFoundGlossaryExc:
                raise EntityNotFound("Glossary not found")

        if len(glossary_ids) != len(glossaries):
            raise EntityNotFound("Not all glossaries were found")

        self.__query.set_project_glossaries(project, glossaries)
        return StatusMessage(message="Glossary list updated")

    def get_translation_memories(self, project_id: int) -> ProjectTranslationMemory:
        """
        Get translation memories for a project.

        Args:
            project_id: Project ID

        Returns:
            ProjectTranslationMemory object with project_id and translation_memories

        Raises:
            EntityNotFound: If project not found
        """
        try:
            project = self.__query._get_project(project_id)
            return ProjectTranslationMemory(
                id=project.id,
                translation_memories=[
                    ProjectTm(
                        memory=TranslationMemory.model_validate(x.memory),
                        mode=x.mode,
                    )
                    for x in project.tm_associations
                ],
            )
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

    def set_translation_memories(
        self, project_id: int, tms_update: ProjectTmUpdate
    ) -> StatusMessage:
        """
        Set translation memories for a project.

        Args:
            project_id: Project ID
            tms_update: ProjectTmUpdate schema with translation memories and modes

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If project or TMs not found
        """
        # Extract tm_ids and modes from the schema
        tm_ids = [tm.id for tm in tms_update.translation_memories]
        # Convert string modes to TmMode enum values
        modes = [TmMode(tm.mode) for tm in tms_update.translation_memories]

        # check writes count
        write_count = 0
        for mode in modes:
            write_count += mode == TmMode.write

        if write_count > 1:
            raise BusinessLogicError(
                "Only one translation memory can be set to write mode",
            )

        try:
            project = self.__query._get_project(project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

        if not tm_ids:
            tms = []
        else:
            mems = set(tm_ids)
            tms = list(self.__tm_query.get_memories_by_id(mems))
            if len(mems) != len(tms):
                raise EntityNotFound("Not all translation memories were found")

        # Create list of (memory, mode) tuples
        tm_modes = []
        for setting in tms_update.translation_memories:
            memory = next((m for m in tms if m.id == setting.id), None)
            if memory:
                tm_modes.append((memory, setting.mode))

        self.__query.set_project_translation_memories(project, tm_modes)
        return StatusMessage(message="Translation memory list updated")

    def search_tm(self, project_id: int, query: str) -> TranslationMemoryListResponse:
        """
        Search translation memories in a project.

        Args:
            project_id: Project ID
            query: Search query string

        Returns:
            TranslationMemoryListResponse with search results

        Raises:
            EntityNotFound: If project not found
        """
        try:
            self.__query._get_project(project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

        # Get TMs from project
        tms_data = self.get_translation_memories(project_id)
        tm_ids = [item.memory.id for item in tms_data.translation_memories]

        if not tm_ids:
            return TranslationMemoryListResponse(records=[], page=0, total_records=0)

        records, count = self.__tm_query.get_memory_records_paged(
            memory_ids=tm_ids,
            page=0,
            page_records=20,
            query=query,
        )

        return TranslationMemoryListResponse(
            records=records, page=0, total_records=count
        )

    def search_tm_similar(
        self, project_id: int, query: str
    ) -> TranslationMemoryListSimilarResponse:
        """
        Search similar translation memories in a project.

        Args:
            project_id: Project ID
            query: Search query string

        Returns:
            TranslationMemoryListSimilarResponse with similar search results

        Raises:
            EntityNotFound: If project not found
        """
        try:
            self.__query._get_project(project_id)
        except NotFoundProjectExc:
            raise EntityNotFound("Project", project_id)

        # Get TMs from project
        tms_data = self.get_translation_memories(project_id)
        tm_ids = [item.memory.id for item in tms_data.translation_memories]

        if not tm_ids:
            return TranslationMemoryListSimilarResponse(
                records=[], page=0, total_records=0
            )

        records = self.__tm_query.get_memory_records_paged_similar(
            memory_ids=tm_ids, page_records=20, query=query
        )

        return TranslationMemoryListSimilarResponse(
            records=records, page=0, total_records=len(records)
        )
