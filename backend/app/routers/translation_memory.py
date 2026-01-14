from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.db import get_db
from app.models import StatusMessage
from app.services import TranslationMemoryService
from app.translation_memory import schema
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/translation_memory", tags=["tms"], dependencies=[Depends(has_user_role)]
)


@router.get("/")
def get_memories(
    db: Annotated[Session, Depends(get_db)],
) -> list[schema.TranslationMemory]:
    service = TranslationMemoryService(db)
    return service.get_memories()


@router.get("/{tm_id}")
def get_memory(
    tm_id: int, db: Annotated[Session, Depends(get_db)]
) -> schema.TranslationMemoryWithRecordsCount:
    service = TranslationMemoryService(db)
    try:
        return service.get_memory(tm_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{tm_id}/records")
def get_memory_records(
    tm_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
    query: Annotated[str | None, Query()] = None,
) -> schema.TranslationMemoryListResponse:
    service = TranslationMemoryService(db)
    if not page:
        page = 0
    try:
        return service.get_memory_records(tm_id, page, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{tm_id}/records/similar")
def get_memory_records_similar(
    tm_id: int,
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query()],
) -> schema.TranslationMemoryListSimilarResponse:
    service = TranslationMemoryService(db)
    try:
        return service.get_memory_records_similar(tm_id, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/upload")
async def create_memory_from_file(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> schema.TranslationMemory:
    service = TranslationMemoryService(db)
    return await service.create_memory_from_file(
        file.filename, await file.read(), current_user
    )


@router.post(
    "/",
    response_model=schema.TranslationMemory,
    status_code=status.HTTP_201_CREATED,
)
def create_translation_memory(
    settings: schema.TranslationMemoryCreationSettings,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
):
    service = TranslationMemoryService(db)
    return service.create_memory(settings.name, current_user)


@router.delete("/{tm_id}")
def delete_memory(tm_id: int, db: Annotated[Session, Depends(get_db)]) -> StatusMessage:
    service = TranslationMemoryService(db)
    try:
        return service.delete_memory(tm_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{tm_id}/download",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/octet-stream": {"schema": {"type": "string"}}},
        }
    },
)
def download_memory(tm_id: int, db: Annotated[Session, Depends(get_db)]):
    service = TranslationMemoryService(db)
    try:
        data = service.download_memory(tm_id)
        return StreamingResponse(
            data.content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{data.filename}"'},
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
