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


def get_service(db: Annotated[Session, Depends(get_db)]):
    return TranslationMemoryService(db)


@router.get("/")
def get_memories(
    service: Annotated[TranslationMemoryService, Depends(get_service)],
) -> list[schema.TranslationMemory]:
    return service.get_memories()


@router.get("/{tm_id}")
def get_memory(
    tm_id: int, service: Annotated[TranslationMemoryService, Depends(get_service)]
) -> schema.TranslationMemoryWithRecordsCount:
    try:
        return service.get_memory(tm_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{tm_id}/records")
def get_memory_records(
    tm_id: int,
    service: Annotated[TranslationMemoryService, Depends(get_service)],
    page: Annotated[int | None, Query(ge=0)] = None,
    query: Annotated[str | None, Query()] = None,
) -> schema.TranslationMemoryListResponse:
    if not page:
        page = 0
    try:
        return service.get_memory_records(tm_id, page, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{tm_id}/records/similar")
def get_memory_records_similar(
    tm_id: int,
    service: Annotated[TranslationMemoryService, Depends(get_service)],
    query: Annotated[str, Query()],
) -> schema.TranslationMemoryListSimilarResponse:
    try:
        return service.get_memory_records_similar(tm_id, query)
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/upload")
async def create_memory_from_file(
    file: Annotated[UploadFile, File()],
    service: Annotated[TranslationMemoryService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> schema.TranslationMemory:
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
    service: Annotated[TranslationMemoryService, Depends(get_service)],
    current_user: Annotated[int, Depends(get_current_user_id)],
):
    return service.create_memory(settings.name, current_user)


@router.delete("/{tm_id}")
def delete_memory(
    tm_id: int, service: Annotated[TranslationMemoryService, Depends(get_service)]
) -> StatusMessage:
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
def download_memory(
    tm_id: int, service: Annotated[TranslationMemoryService, Depends(get_service)]
):
    try:
        data = service.download_memory(tm_id)
        return StreamingResponse(
            data.content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{data.filename}"'},
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
