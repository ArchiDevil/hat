from typing import Annotated, Final

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

import app.translation_memory.models as tm_models
import app.translation_memory.schema as tm_schema
from app import models
from app.db import get_db
from app.formats.tmx import extract_tmx_content
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
def get_translation_memories(
    db: Annotated[Session, Depends(get_db)],
) -> list[tm_schema.TranslationMemory]:
    return [
        tm_schema.TranslationMemory(id=doc.id, name=doc.name, created_by=doc.created_by)
        for doc in TranslationMemoryQuery(db).get_memories()
    ]


@router.get("/{tm_id}")
def get_translation_memory(
    tm_id: int, db: Annotated[Session, Depends(get_db)]
) -> tm_schema.TranslationMemoryWithRecordsCount:
    doc = get_memory_by_id(db, tm_id)
    return tm_schema.TranslationMemoryWithRecordsCount(
        id=doc.id,
        name=doc.name,
        created_by=doc.created_by,
        records_count=TranslationMemoryQuery(db).get_memory_records_count(tm_id),
    )


@router.get("/{tm_id}/records")
def get_translation_memory_records(
    tm_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[tm_schema.TranslationMemoryRecord]:
    page_records: Final = 100
    if not page:
        page = 0

    get_memory_by_id(db, tm_id)
    return [
        tm_schema.TranslationMemoryRecord(
            id=record.id, source=record.source, target=record.target
        )
        for record in TranslationMemoryQuery(db).get_memory_records_paged(
            tm_id, page, page_records
        )
    ]


@router.post("/")
async def create_translation_memory(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> tm_schema.TranslationMemory:
    name = file.filename
    tm_data = await file.read()
    segments = extract_tmx_content(tm_data)

    doc = TranslationMemoryQuery(db).add_memory(
        name or "",
        current_user,
        [
            tm_models.TranslationMemoryRecord(
                source=segment.original,
                target=segment.translation,
                creation_date=segment.creation_date,
                change_date=segment.change_date,
            )
            for segment in segments
        ],
    )

    return tm_schema.TranslationMemory(
        id=doc.id, name=doc.name, created_by=doc.created_by
    )


@router.delete("/{tm_id}")
def delete_translation_memory(
    tm_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    TranslationMemoryQuery(db).delete_memory(get_memory_by_id(db, tm_id))
    return models.StatusMessage(message="Deleted")
