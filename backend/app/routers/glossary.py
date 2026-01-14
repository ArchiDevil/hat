from typing import Annotated, Final

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.db import get_db
from app.glossary.models import ProcessingStatuses
from app.glossary.schema import (
    GlossaryLoadFileResponse,
    GlossaryRecordCreate,
    GlossaryRecordResponse,
    GlossaryRecordSchema,
    GlossaryRecordUpdate,
    GlossaryResponse,
    GlossarySchema,
)
from app.glossary.tasks import create_glossary_from_file_tasks
from app.models import StatusMessage
from app.services import GlossaryService
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/glossary", tags=["glossary"], dependencies=[Depends(has_user_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return GlossaryService(db)


@router.get(
    "/",
    description="Get a glossary list",
    response_model=list[GlossaryResponse],
    status_code=status.HTTP_200_OK,
)
def list_glossary(service: Annotated[GlossaryService, Depends(get_service)]):
    return service.list_glossaries()


@router.get(
    path="/{glossary_id}",
    description="Get a single glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary with id 1 not found"}
                }
            },
        },
    },
)
def retrieve_glossary(
    glossary_id: int, service: Annotated[GlossaryService, Depends(get_service)]
):
    try:
        return service.get_glossary(glossary_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/",
    description="Create glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary(
    glossary: GlossarySchema,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[GlossaryService, Depends(get_service)],
):
    return service.create_glossary(
        data=glossary,
        processing_status=ProcessingStatuses.DONE,
        user_id=user_id,
    )


@router.put(
    path="/{glossary_id}",
    description="Update a single glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary with id 1 not found"}
                }
            },
        },
    },
)
def update_glossary(
    glossary_id: int,
    glossary: GlossarySchema,
    service: Annotated[GlossaryService, Depends(get_service)],
):
    try:
        return service.update_glossary(glossary_id, glossary)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    path="/{glossary_id}",
    description="Delete a single glossary",
    response_model=StatusMessage,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary with id 1 not found"}
                }
            },
        },
    },
)
def delete_glossary(
    glossary_id: int, service: Annotated[GlossaryService, Depends(get_service)]
):
    try:
        return service.delete_glossary(glossary_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{glossary_id}/records",
    description="Get list glossary record",
    response_model=GlossaryRecordResponse,
    status_code=status.HTTP_200_OK,
)
def list_records(
    glossary_id: int,
    service: Annotated[GlossaryService, Depends(get_service)],
    page: Annotated[int | None, Query(ge=0)] = None,
    search: Annotated[str | None, Query()] = None,
):
    page_records: Final = 100
    if not page:
        page = 0

    try:
        return service.list_glossary_records(glossary_id, page, page_records, search)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{glossary_id}/records",
    description="Create glossary record",
    response_model=GlossaryRecordSchema,
    status_code=status.HTTP_200_OK,
)
def create_glossary_record(
    glossary_id: int,
    record: GlossaryRecordCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[GlossaryService, Depends(get_service)],
):
    try:
        return service.create_glossary_record(glossary_id, record, user_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    path="/records/{record_id}",
    description="Update a single glossary record",
    response_model=GlossaryRecordSchema,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary record requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary record with id 1 not found"}
                }
            },
        },
    },
)
def update_glossary_record(
    record_id: int,
    record: GlossaryRecordUpdate,
    service: Annotated[GlossaryService, Depends(get_service)],
):
    try:
        return service.update_glossary_record(record_id, record)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    path="/records/{record_id}",
    description="Delete a single glossary record",
    response_model=StatusMessage,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary record requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary record with id 1 not found"}
                }
            },
        },
    },
)
def delete_glossary_record(
    record_id: int, service: Annotated[GlossaryService, Depends(get_service)]
):
    try:
        return service.delete_glossary_record(record_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/load_file",
    description="Load xlsx glossary file",
    response_model=GlossaryLoadFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary_from_file(
    user_id: Annotated[int, Depends(get_current_user_id)],
    glossary_name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[GlossaryService, Depends(get_service)],
):
    sheet, glossary = service.create_glossary_from_file(
        file=file, user_id=user_id, glossary_name=glossary_name
    )
    background_tasks.add_task(
        create_glossary_from_file_tasks,
        user_id=user_id,
        sheet=sheet,
        db=db,
        glossary_id=glossary.id,
    )
    return GlossaryLoadFileResponse(glossary_id=glossary.id)
