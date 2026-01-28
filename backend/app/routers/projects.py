from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound, UnauthorizedAccess
from app.db import get_db
from app.models import StatusMessage
from app.projects.schema import (
    DetailedProjectResponse,
    ProjectCreate,
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
