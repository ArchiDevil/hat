from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound, UnauthorizedAccess
from app.db import get_db
from app.glossary.schema import GlossaryRecordSchema
from app.models import StatusMessage
from app.projects.schema import (
    DetailedProjectResponse,
    ProjectCreate,
    ProjectGlossary,
    ProjectGlossaryUpdate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/projects", tags=["projects"], dependencies=[Depends(has_user_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return ProjectService(db)


@router.get(
    "/",
    description="Get a project list",
    response_model=list[ProjectResponse],
)
def list_projects(
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_service)],
):
    return service.list_projects(user_id)


@router.get(
    path="/{project_id}",
    description="Get a single project",
    response_model=DetailedProjectResponse,
    responses={
        404: {
            "description": "Project requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def retrieve_project(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_service)],
):
    try:
        return service.get_project(project_id, user_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UnauthorizedAccess as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/",
    description="Create project",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: ProjectCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_service)],
):
    return service.create_project(project, user_id)


@router.put(
    path="/{project_id}",
    description="Update a single project",
    response_model=ProjectResponse,
    responses={
        404: {
            "description": "Project requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_service)],
):
    try:
        return service.update_project(project_id, project, user_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UnauthorizedAccess as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    path="/{project_id}",
    description="Delete a single project",
    response_model=StatusMessage,
    responses={
        404: {
            "description": "Project requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def delete_project(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_service)],
):
    try:
        return service.delete_project(project_id, user_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UnauthorizedAccess as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/{project_id}/glossaries",
    description="Get glossaries for a project",
    response_model=ProjectGlossary,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Project requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def get_project_glossaries(
    project_id: int,
    service: Annotated[ProjectService, Depends(get_service)],
):
    try:
        return service.get_glossaries(project_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{project_id}/glossaries",
    description="Set glossaries for a project",
    response_model=StatusMessage,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Project or glossaries not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def set_project_glossaries(
    project_id: int,
    glossaries: ProjectGlossaryUpdate,
    service: Annotated[ProjectService, Depends(get_service)],
):
    try:
        return service.set_glossaries(project_id, glossaries.glossaries)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{project_id}/glossary_search",
    description="Search glossaries for a project",
    response_model=list[GlossaryRecordSchema],
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Project requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 1 not found"}
                }
            },
        },
    },
)
def project_glossary_search(
    project_id: int,
    query: Annotated[str, Query()],
    service: Annotated[ProjectService, Depends(get_service)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        from app.glossary.query import GlossaryQuery

        glossary_query = GlossaryQuery(db)
        # Get glossaries from project
        proj_glossaries = service.get_glossaries(project_id)
        glossary_ids = [item.id for item in proj_glossaries.glossaries]

        if not glossary_ids:
            return []

        records = glossary_query.get_glossary_records_for_phrase(query, glossary_ids)
        return [GlossaryRecordSchema.model_validate(record) for record in records]
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
