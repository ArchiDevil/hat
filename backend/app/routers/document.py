from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import BusinessLogicError, EntityNotFound
from app.comments.schema import CommentCreate, CommentResponse
from app.db import get_db
from app.documents import schema as doc_schema
from app.glossary.schema import GlossaryRecordSchema
from app.services import DocumentService
from app.translation_memory.schema import (
    MemorySubstitution,
    TranslationMemoryListResponse,
    TranslationMemoryListSimilarResponse,
)
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/document", tags=["document"], dependencies=[Depends(has_user_role)]
)


@router.get("/")
def get_docs(
    db: Annotated[Session, Depends(get_db)],
) -> list[doc_schema.DocumentWithRecordsCount]:
    service = DocumentService(db)
    return service.get_documents()


@router.get("/{doc_id}")
def get_doc(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> doc_schema.DocumentWithRecordsCount:
    service = DocumentService(db)
    try:
        return service.get_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/records")
def get_doc_records(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
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

    service = DocumentService(db)
    try:
        return service.get_document_records(doc_id, page, filters)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/glossary_search")
def doc_glossary_search(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query()],
) -> list[GlossaryRecordSchema]:
    service = DocumentService(db)
    try:
        return service.doc_glossary_search(doc_id, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/records/{record_id}/comments")
def get_comments(
    record_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> list[CommentResponse]:
    """Get all comments for a document record"""
    service = DocumentService(db)
    try:
        return service.get_comments(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/records/{record_id}/comments")
def create_comment(
    record_id: int,
    comment_data: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> CommentResponse:
    """Create a new comment for a document record"""
    service = DocumentService(db)
    try:
        return service.create_comment(record_id, comment_data, current_user)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/records/{record_id}/substitutions")
def get_record_substitutions(
    record_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[MemorySubstitution]:
    service = DocumentService(db)
    try:
        return service.get_record_substitutions(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/records/{record_id}/glossary_records")
def get_record_glossary_records(
    record_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[GlossaryRecordSchema]:
    service = DocumentService(db)
    try:
        return service.get_record_glossary_records(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/records/{record_id}")
def update_doc_record(
    record_id: int,
    record: doc_schema.DocumentRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> doc_schema.DocumentRecordUpdateResponse:
    service = DocumentService(db)
    try:
        return service.update_record(record_id, record)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/memories")
def get_translation_memories(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[doc_schema.DocTranslationMemory]:
    service = DocumentService(db)
    try:
        return service.get_translation_memories(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{doc_id}/memories")
def set_translation_memories(
    doc_id: int,
    settings: doc_schema.DocTranslationMemoryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    service = DocumentService(db)
    try:
        return service.set_translation_memories(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doc_id}/tm/exact")
def search_tm_exact(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListResponse:
    service = DocumentService(db)
    try:
        return service.search_tm_exact(doc_id, source)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/tm/similar")
def search_tm_similar(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListSimilarResponse:
    service = DocumentService(db)
    try:
        return service.search_tm_similar(doc_id, source)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{doc_id}/glossaries")
def get_glossaries(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[doc_schema.DocGlossary]:
    service = DocumentService(db)
    try:
        return service.get_glossaries(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{doc_id}/glossaries")
def set_glossaries(
    doc_id: int,
    settings: doc_schema.DocGlossaryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    service = DocumentService(db)
    try:
        return service.set_glossaries(doc_id, settings)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{doc_id}")
def delete_doc(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    service = DocumentService(db)
    try:
        return service.delete_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/")
async def create_doc(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> doc_schema.Document:
    service = DocumentService(db)
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
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    service = DocumentService(db)
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
def download_doc(doc_id: int, db: Annotated[Session, Depends(get_db)]):
    service = DocumentService(db)
    try:
        return service.download_document(doc_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
