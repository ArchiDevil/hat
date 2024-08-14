from typing import Annotated, Final

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.formats.tmx import extract_tmx_content
from app.models import StatusMessage
from app.translation_memory import models, schema
from app.translation_memory.query import TranslationMemoryQuery
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/translation_memory", tags=["tms"], dependencies=[Depends(has_user_role)]
)


def get_memory_by_id(db: Session, memory_id: int):
    doc = TranslationMemoryQuery(db).get_memory(memory_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return doc


@router.get("/")
def get_memories(
    db: Annotated[Session, Depends(get_db)],
) -> list[schema.TranslationMemory]:
    return [
        schema.TranslationMemory(id=doc.id, name=doc.name, created_by=doc.created_by)
        for doc in TranslationMemoryQuery(db).get_memories()
    ]


@router.get("/{tm_id}")
def get_memory(
    tm_id: int, db: Annotated[Session, Depends(get_db)]
) -> schema.TranslationMemoryWithRecordsCount:
    doc = get_memory_by_id(db, tm_id)
    return schema.TranslationMemoryWithRecordsCount(
        id=doc.id,
        name=doc.name,
        created_by=doc.created_by,
        records_count=TranslationMemoryQuery(db).get_memory_records_count(tm_id),
    )


@router.get("/{tm_id}/records")
def get_memory_records(
    tm_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[schema.TranslationMemoryRecord]:
    page_records: Final = 100
    if not page:
        page = 0

    get_memory_by_id(db, tm_id)
    return [
        schema.TranslationMemoryRecord(
            id=record.id, source=record.source, target=record.target
        )
        for record in TranslationMemoryQuery(db).get_memory_records_paged(
            tm_id, page, page_records
        )
    ]


@router.post("/upload")
async def create_memory_from_file(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> schema.TranslationMemory:
    name = file.filename
    tm_data = await file.read()
    segments = extract_tmx_content(tm_data)

    doc = TranslationMemoryQuery(db).add_memory(
        name or "",
        current_user,
        [
            models.TranslationMemoryRecord(
                source=segment.original,
                target=segment.translation,
                creation_date=segment.creation_date,
                change_date=segment.change_date,
            )
            for segment in segments
        ],
    )

    return schema.TranslationMemory(id=doc.id, name=doc.name, created_by=doc.created_by)


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
    doc = TranslationMemoryQuery(db).add_memory(settings.name, current_user, [])
    return schema.TranslationMemory(id=doc.id, name=doc.name, created_by=doc.created_by)


@router.delete("/{tm_id}")
def delete_memory(tm_id: int, db: Annotated[Session, Depends(get_db)]) -> StatusMessage:
    TranslationMemoryQuery(db).delete_memory(get_memory_by_id(db, tm_id))
    return StatusMessage(message="Deleted")
