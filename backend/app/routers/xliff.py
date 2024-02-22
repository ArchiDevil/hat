from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_fastapi import get_db
from app import schema
from app.xliff import extract_xliff_content
from .models import XliffFile, XliffFileWithRecords, XliffFileRecord, StatusMessage


router = APIRouter(prefix="/xliff", tags=["xliff"])


@router.get("/")
def get_xliffs(db: Session = Depends(get_db)) -> list[XliffFile]:
    xliffs = db.query(schema.XliffDocument).all()
    return [XliffFile(id=xliff.id, name=xliff.name) for xliff in xliffs]


@router.get("/{doc_id}")
def get_xliff(doc_id: int, db: Session = Depends(get_db)) -> XliffFileWithRecords:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return XliffFileWithRecords(
        id=doc.id,
        name=doc.name,
        records=[
            XliffFileRecord(
                id=record.id,
                segment_id=record.segment_id,
                source=record.source,
                target=record.target,
            )
            for record in doc.records
        ],
    )


@router.delete("/{doc_id}")
def delete_xliff(doc_id: int, db: Session = Depends(get_db)) -> StatusMessage:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    db.delete(doc)
    db.commit()
    return StatusMessage(message="Deleted")


@router.post("/")
async def create_xliff(
    file: Annotated[UploadFile, File()], db: Session = Depends(get_db)
) -> XliffFile:
    name = file.filename
    xliff_data = await file.read()
    original_document = xliff_data.decode("utf-8")
    xliff_data = extract_xliff_content(xliff_data)

    doc = schema.XliffDocument(name=name, original_document=original_document)
    db.add(doc)

    for segment in xliff_data.segments:
        if not segment.approved:
            tmx_data = db.execute(
                select(schema.TmxRecord.source, schema.TmxRecord.target)
                .where(schema.TmxRecord.source == segment.original)
                .limit(1)
            ).first()
            if tmx_data:
                segment.translation = tmx_data.target
                segment.approved = True

        doc.records.append(
            schema.XliffRecord(
                segment_id=segment.id_,
                source=segment.original,
                target=segment.translation,
            )
        )

    db.commit()

    new_doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc.id).first()
    )
    assert new_doc

    return XliffFile(id=new_doc.id, name=new_doc.name)


@router.get("/{doc_id}/download")
def download_xliff(doc_id: int):
    # TODO: implement this
    pass
