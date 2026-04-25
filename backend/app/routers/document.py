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
from app.permissions import P, PermissionChecker
from app.services import DocumentService
from app.user.depends import get_current_user_id

router = APIRouter(
    prefix="/document",
    tags=["document"],
    dependencies=[Depends(PermissionChecker(P.DOCUMENT_READ))],
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


@router.get(
    "/{doc_id}/records", dependencies=[Depends(PermissionChecker(P.RECORD_READ))]
)
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


@router.get(
    "/{doc_id}/first_unapproved",
    dependencies=[Depends(PermissionChecker(P.RECORD_READ))],
)
def get_first_unapproved(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
) -> doc_schema.DocumentRecord | None:
    try:
        return service.get_first_unapproved_record(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{doc_id}/record_page", dependencies=[Depends(PermissionChecker(P.RECORD_READ))]
)
def get_record_page(
    doc_id: int,
    record_id: Annotated[int, Query(ge=1)],
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
        return service.get_record_page(doc_id, record_id, filters)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{doc_id}", dependencies=[Depends(PermissionChecker(P.DOCUMENT_DELETE))]
)
def delete_doc(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
) -> models.StatusMessage:
    try:
        return service.delete_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", dependencies=[Depends(PermissionChecker(P.DOCUMENT_CREATE))])
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


@router.post(
    "/{doc_id}/process", dependencies=[Depends(PermissionChecker(P.DOCUMENT_PROCESS))]
)
def process_doc(
    doc_id: int,
    settings: doc_schema.DocumentProcessingSettings,
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.process_document(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{doc_id}/match", dependencies=[Depends(PermissionChecker(P.DOCUMENT_PROCESS))]
)
async def match_doc(
    doc_id: int,
    file_to_match: Annotated[UploadFile, File()],
    api_key: Annotated[str, Form()],
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return await service.match_document(doc_id, file_to_match, api_key)
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
    dependencies=[Depends(PermissionChecker(P.DOCUMENT_DOWNLOAD))],
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
    dependencies=[Depends(PermissionChecker(P.DOCUMENT_DOWNLOAD))],
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
    dependencies=[Depends(PermissionChecker(P.DOCUMENT_DOWNLOAD))],
)
def download_xliff(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
):
    try:
        return service.download_xliff(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{doc_id}", dependencies=[Depends(PermissionChecker(P.DOCUMENT_UPDATE))])
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


@router.post(
    "/upload_xliff", dependencies=[Depends(PermissionChecker(P.DOCUMENT_UPDATE))]
)
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
