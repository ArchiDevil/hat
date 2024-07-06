from typing import Annotated, Final

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.orm import Session

from app import schema, models
from app.auth import has_user_role, get_current_user_id
from app.db import get_db
from app.tmx import extract_tmx_content


router = APIRouter(prefix="/tmx", tags=["tmx"], dependencies=[Depends(has_user_role)])


@router.get("/")
def get_tmxs(db: Annotated[Session, Depends(get_db)]) -> list[models.TmxFile]:
    docs = db.query(schema.TmxDocument).order_by(schema.TmxDocument.id).all()
    return [
        models.TmxFile(id=doc.id, name=doc.name, created_by=doc.created_by)
        for doc in docs
    ]


@router.get("/{tmx_id}")
def get_tmx(
    tmx_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.TmxFileWithRecordsCount:
    doc = db.query(schema.TmxDocument).filter(schema.TmxDocument.id == tmx_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records_count = (
        db.query(schema.TmxRecord).filter(schema.TmxRecord.document == doc).count()
    )

    return models.TmxFileWithRecordsCount(
        id=doc.id, name=doc.name, created_by=doc.created_by, records_count=records_count
    )


@router.get("/{tmx_id}/records")
def get_tmx_records(
    tmx_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[models.TmxFileRecord]:
    page_records: Final = 100
    if not page:
        page = 0

    doc = db.query(schema.TmxDocument).filter(schema.TmxDocument.id == tmx_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records = (
        db.query(schema.TmxRecord)
        .filter(schema.TmxRecord.document_id == tmx_id)
        .order_by(schema.TmxRecord.id)
        .offset(page_records * page)
        .limit(page_records)
        .all()
    )
    return [
        models.TmxFileRecord(id=record.id, source=record.source, target=record.target)
        for record in records
    ]


@router.post("/")
async def create_tmx(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> models.TmxFile:
    name = file.filename
    tmx_data = await file.read()
    segments = extract_tmx_content(tmx_data)

    doc = schema.TmxDocument(
        name=name,
        created_by=current_user,
    )
    db.add(doc)
    db.commit()

    for segment in segments:
        doc.records.append(
            schema.TmxRecord(
                source=segment.original,
                target=segment.translation,
                creation_date=segment.creation_date if segment.creation_date else None,
                change_date=segment.change_date if segment.change_date else None,
            )
        )
    db.commit()

    new_doc = (
        db.query(schema.TmxDocument).filter(schema.TmxDocument.id == doc.id).first()
    )
    assert new_doc

    return models.TmxFile(id=new_doc.id, name=new_doc.name, created_by=doc.created_by)


@router.delete("/{tmx_id}")
def delete_tmx(
    tmx_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    doc = db.query(schema.TmxDocument).filter(schema.TmxDocument.id == tmx_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    db.delete(doc)
    db.commit()
    return models.StatusMessage(message="Deleted")
