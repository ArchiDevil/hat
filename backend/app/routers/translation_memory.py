from typing import Annotated, Final

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.formats.tmx import extract_tmx_content
import app.translation_memory.models as tm_models
import app.translation_memory.schema as tm_schema
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/translation_memory", tags=["tms"], dependencies=[Depends(has_user_role)]
)


@router.get("/")
def get_tmxs(
    db: Annotated[Session, Depends(get_db)],
) -> list[tm_schema.TranslationMemory]:
    docs = (
        db.query(tm_models.TranslationMemory)
        .order_by(tm_models.TranslationMemory.id)
        .all()
    )
    return [
        tm_schema.TranslationMemory(id=doc.id, name=doc.name, created_by=doc.created_by)
        for doc in docs
    ]


@router.get("/{tmx_id}")
def get_tmx(
    tmx_id: int, db: Annotated[Session, Depends(get_db)]
) -> tm_schema.TranslationMemoryWithRecordsCount:
    doc = (
        db.query(tm_models.TranslationMemory)
        .filter(tm_models.TranslationMemory.id == tmx_id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records_count = (
        db.query(tm_models.TranslationMemoryRecord)
        .filter(tm_models.TranslationMemoryRecord.document == doc)
        .count()
    )

    return tm_schema.TranslationMemoryWithRecordsCount(
        id=doc.id, name=doc.name, created_by=doc.created_by, records_count=records_count
    )


@router.get("/{tmx_id}/records")
def get_tmx_records(
    tmx_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[tm_schema.TranslationMemoryRecord]:
    page_records: Final = 100
    if not page:
        page = 0

    doc = (
        db.query(tm_models.TranslationMemory)
        .filter(tm_models.TranslationMemory.id == tmx_id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records = (
        db.query(tm_models.TranslationMemoryRecord)
        .filter(tm_models.TranslationMemoryRecord.document_id == tmx_id)
        .order_by(tm_models.TranslationMemoryRecord.id)
        .offset(page_records * page)
        .limit(page_records)
        .all()
    )
    return [
        tm_schema.TranslationMemoryRecord(
            id=record.id, source=record.source, target=record.target
        )
        for record in records
    ]


@router.post("/")
async def create_tmx(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> tm_schema.TranslationMemory:
    name = file.filename
    tmx_data = await file.read()
    segments = extract_tmx_content(tmx_data)

    doc = tm_models.TranslationMemory(
        name=name,
        created_by=current_user,
    )
    db.add(doc)
    db.commit()

    for segment in segments:
        doc.records.append(
            tm_models.TranslationMemoryRecord(
                source=segment.original,
                target=segment.translation,
                creation_date=segment.creation_date if segment.creation_date else None,
                change_date=segment.change_date if segment.change_date else None,
            )
        )
    db.commit()

    new_doc = (
        db.query(tm_models.TranslationMemory)
        .filter(tm_models.TranslationMemory.id == doc.id)
        .first()
    )
    assert new_doc

    return tm_schema.TranslationMemory(
        id=new_doc.id, name=new_doc.name, created_by=doc.created_by
    )


@router.delete("/{tmx_id}")
def delete_tmx(
    tmx_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    doc = (
        db.query(tm_models.TranslationMemory)
        .filter(tm_models.TranslationMemory.id == tmx_id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    db.delete(doc)
    db.commit()
    return models.StatusMessage(message="Deleted")
