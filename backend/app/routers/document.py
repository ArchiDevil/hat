from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import BusinessLogicError, EntityNotFound, UnauthorizedAccess
from app.db import get_db
from app.documents import schema as doc_schema
from app.services import DocumentService
from app.user.depends import get_current_user_id, has_admin_role, has_user_role

router = APIRouter(
    prefix="/document", tags=["document"], dependencies=[Depends(has_user_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return DocumentService(db)


@router.get("/{doc_id}")
def get_doc(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
) -> doc_schema.DocumentWithRecordsCount:
    try:
        return service.get_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/records")
def get_doc_records(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
    page: Annotated[int | None, Query(ge=0)] = None,
    source: Annotated[
        str | None, Query(description="Filter by source text (contains search)")
    ] = None,
    target: Annotated[
        str | None, Query(description="Filter by target text (contains search)")
    ] = None,
) -> doc_schema.DocumentRecordListResponse:
    if not page:
        page = 0

    filters = None
    if source or target:
        filters = doc_schema.DocumentRecordFilter(
            source_filter=source, target_filter=target
        )

    try:
        return service.get_document_records(doc_id, page, filters)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/records/row_page")
def get_row_page(
    doc_id: int,
    row: Annotated[int, Query(ge=1)],
    service: Annotated[DocumentService, Depends(get_service)],
    source: Annotated[
        str | None, Query(description="Filter by source text (contains search)")
    ] = None,
    target: Annotated[
        str | None, Query(description="Filter by target text (contains search)")
    ] = None,
) -> doc_schema.RowPageResponse:
    filters = None
    if source or target:
        filters = doc_schema.DocumentRecordFilter(
            source_filter=source, target_filter=target
        )

    try:
        return service.get_row_page(doc_id, row, filters)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{doc_id}", dependencies=[Depends(has_admin_role)])
def delete_doc(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
) -> models.StatusMessage:
    try:
        return service.delete_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", dependencies=[Depends(has_admin_role)])
async def create_doc(
    file: Annotated[UploadFile, File()],
    service: Annotated[DocumentService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
    project_id: Annotated[int, Form()],
) -> doc_schema.Document:
    try:
        return await service.create_document(file, current_user, project_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{doc_id}/process", dependencies=[Depends(has_admin_role)])
def process_doc(
    doc_id: int,
    settings: doc_schema.DocumentProcessingSettings,
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.process_document(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{doc_id}/download",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/octet-stream": {"schema": {"type": "string"}}},
        }
    },
    dependencies=[Depends(has_admin_role)],
)
def download_doc(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
):
    try:
        return service.download_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{doc_id}/download_original",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/octet-stream": {"schema": {"type": "string"}}},
        }
    },
    dependencies=[Depends(has_admin_role)],
)
def download_original_doc(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
):
    try:
        return service.download_original_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{doc_id}/download_xliff",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/octet-stream": {"schema": {"type": "string"}}},
        }
    },
    dependencies=[Depends(has_admin_role)],
)
def download_xliff(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
):
    try:
        return service.download_xliff(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{doc_id}", dependencies=[Depends(has_admin_role)])
def update_document(
    doc_id: int,
    update_data: doc_schema.DocumentUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[DocumentService, Depends(get_service)],
) -> doc_schema.DocumentUpdateResponse:
    try:
        return service.update_document(doc_id, update_data, user_id)
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


@router.post("/upload_xliff", dependencies=[Depends(has_admin_role)])
async def upload_xliff(
    service: Annotated[DocumentService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
    file: Annotated[UploadFile, File()],
    update_approved: Annotated[bool, Form()] = False,
) -> models.StatusMessage:
    try:
        return await service.upload_xliff(
            file,
            doc_schema.XliffUploadOptions(update_approved=update_approved),
            current_user,
        )
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
