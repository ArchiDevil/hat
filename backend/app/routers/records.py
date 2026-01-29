from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.comments.schema import CommentCreate, CommentResponse
from app.db import get_db
from app.documents import schema as doc_schema
from app.documents.models import DocumentRecordHistoryChangeType
from app.glossary.schema import GlossaryRecordSchema
from app.services.record_service import RecordService
from app.translation_memory.schema import MemorySubstitution
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/records", tags=["records"], dependencies=[Depends(has_user_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return RecordService(db)


@router.put("/{record_id}")
def update_doc_record(
    record_id: int,
    record: doc_schema.DocumentRecordUpdate,
    service: Annotated[RecordService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> doc_schema.DocumentRecordUpdateResponse:
    try:
        return service.update_record(
            record_id, record, current_user, DocumentRecordHistoryChangeType.manual_edit
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{record_id}/comments")
def get_comments(
    record_id: int,
    service: Annotated[RecordService, Depends(get_service)],
) -> list[CommentResponse]:
    try:
        return service.get_comments(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{record_id}/comments")
def create_comment(
    record_id: int,
    comment_data: CommentCreate,
    service: Annotated[RecordService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> CommentResponse:
    try:
        return service.create_comment(record_id, comment_data, current_user)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{record_id}/substitutions")
def get_record_substitutions(
    record_id: int,
    service: Annotated[RecordService, Depends(get_service)],
) -> list[MemorySubstitution]:
    try:
        return service.get_record_substitutions(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{record_id}/history",
    description="Get the history of changes for a document record",
)
def get_segment_history(
    record_id: int,
    service: Annotated[RecordService, Depends(get_service)],
) -> doc_schema.DocumentRecordHistoryListResponse:
    try:
        return service.get_segment_history(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{record_id}/glossary_records")
def get_record_glossary_records(
    record_id: int,
    service: Annotated[RecordService, Depends(get_service)],
) -> list[GlossaryRecordSchema]:
    try:
        return service.get_record_glossary_records(record_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
