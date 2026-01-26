from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import BusinessLogicError, EntityNotFound, UnauthorizedAccess
from app.db import get_db
from app.documents import schema as doc_schema
from app.glossary.schema import GlossaryRecordSchema
from app.services import DocumentService
from app.translation_memory.schema import (
    TranslationMemoryListResponse,
    TranslationMemoryListSimilarResponse,
)
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/document", tags=["document"], dependencies=[Depends(has_user_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return DocumentService(db)


@router.get("/")
def get_docs(
    service: Annotated[DocumentService, Depends(get_service)],
) -> list[doc_schema.DocumentWithRecordsCount]:
    return service.get_documents()


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


@router.get("/{doc_id}/glossary_search")
def doc_glossary_search(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
    query: Annotated[str, Query()],
) -> list[GlossaryRecordSchema]:
    try:
        return service.doc_glossary_search(doc_id, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/memories")
def get_translation_memories(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
) -> list[doc_schema.DocTranslationMemory]:
    try:
        return service.get_translation_memories(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{doc_id}/memories")
def set_translation_memories(
    doc_id: int,
    settings: doc_schema.DocTranslationMemoryUpdate,
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.set_translation_memories(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doc_id}/tm/exact")
def search_tm_exact(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListResponse:
    try:
        return service.search_tm_exact(doc_id, source)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/tm/similar")
def search_tm_similar(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListSimilarResponse:
    try:
        return service.search_tm_similar(doc_id, source)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/glossaries")
def get_glossaries(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
) -> list[doc_schema.DocGlossary]:
    try:
        return service.get_glossaries(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{doc_id}/glossaries")
def set_glossaries(
    doc_id: int,
    settings: doc_schema.DocGlossaryUpdate,
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.set_glossaries(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{doc_id}")
def delete_doc(
    doc_id: int,
    service: Annotated[DocumentService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.delete_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/")
async def create_doc(
    file: Annotated[UploadFile, File()],
    service: Annotated[DocumentService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> doc_schema.Document:
    try:
        return await service.create_document(file, current_user)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{doc_id}/process")
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
)
def download_doc(
    doc_id: int, service: Annotated[DocumentService, Depends(get_service)]
):
    try:
        return service.download_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{doc_id}")
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
