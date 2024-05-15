from datetime import datetime, timedelta

# import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schema
from app.db import get_db
from app.xliff import XliffSegment, extract_xliff_content
from .models import (
    XliffFile,
    XliffFileRecord,
    StatusMessage,
    DocumentStatus,
    XliffProcessingSettings,
)

# TODO: add settings for UI when processing
# TODO: add XLIFF segments statuses according to the specification


router = APIRouter(prefix="/xliff", tags=["xliff"])


@router.get("/")
def get_xliffs(db: Annotated[Session, Depends(get_db)]) -> list[XliffFile]:
    xliffs = (
        db.query(schema.XliffDocument)
        .filter(schema.XliffDocument.processing_status != "uploaded")
        .order_by(schema.XliffDocument.id)
        .all()
    )
    return [
        XliffFile(
            id=xliff.id, name=xliff.name, status=DocumentStatus(xliff.processing_status)
        )
        for xliff in xliffs
    ]


@router.get("/{doc_id}")
def get_xliff(doc_id: int, db: Annotated[Session, Depends(get_db)]) -> XliffFile:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return XliffFile(
        id=doc.id,
        name=doc.name,
        status=DocumentStatus(doc.processing_status),
    )


@router.get("/{doc_id}/records")
def get_xliff_records(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[XliffFileRecord]:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return [
        XliffFileRecord(
            id=record.id,
            segment_id=record.segment_id,
            source=record.source,
            target=record.target,
        )
        for record in doc.records
    ]


@router.delete("/{doc_id}")
def delete_xliff(doc_id: int, db: Annotated[Session, Depends(get_db)]) -> StatusMessage:
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
    file: Annotated[UploadFile, File()], db: Annotated[Session, Depends(get_db)]
)  -> XliffFile:
    cutoff_date = datetime.now() - timedelta(days=1)

    # Remove outdated XLIFF files when adding a new one.
    outdated_docs = (
        db.query(schema.XliffDocument)
         .filter(schema.XliffDocument.upload_time < cutoff_date)
         .filter(schema.XliffDocument.processing_status == "uploaded")
         .all()
    )
    for doc in outdated_docs:
        db.delete(doc)
    db.commit()

    name = file.filename
    xliff_data = await file.read()
    original_document = xliff_data.decode("utf-8")

    doc = schema.XliffDocument(
        name=name,
        original_document=original_document,
        processing_status=DocumentStatus.UPLOADED.value,
        upload_time=datetime.now(),
    )
    db.add(doc)
    db.commit()

    new_doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc.id).one()
    )
    return XliffFile(
        id=new_doc.id,
        name=new_doc.name,
        status=DocumentStatus(new_doc.processing_status),
    )


def get_segment_translation(
    segment: XliffSegment,
    settings: XliffProcessingSettings,
    db: Annotated[Session, Depends(get_db)],
):
    # TODO: this is slow, it needs to be optimized
    tmx_data = db.execute(
        select(schema.TmxRecord.source, schema.TmxRecord.target)
        .where(schema.TmxRecord.source == segment.original)
        .limit(1)
    ).first()

    if tmx_data:
        return tmx_data.target
    elif settings.substitute_numbers and segment.original.isdigit():
        return segment.original

    return ""


@router.post("/{doc_id}/process")
def process_xliff(
    doc_id: int,
    settings: XliffProcessingSettings,
    db: Annotated[Session, Depends(get_db)],
) -> StatusMessage:
    doc = db.query(schema.XliffDocument).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # TODO: it should be done when worker is here
    # doc.processing_status = DocumentStatus.PENDING.value
    # db.commit()

    # TODO: move it to worker
    doc.processing_status = DocumentStatus.PROCESSING.value
    db.commit()

    xliff_data = extract_xliff_content(doc.original_document.encode())
    for segment in xliff_data.segments:
        if not segment.approved:
            segment.translation = get_segment_translation(segment, settings, db)

        doc.records.append(
            schema.XliffRecord(
                segment_id=segment.id_,
                source=segment.original,
                target=segment.translation,
            )
        )

    doc.processing_status = DocumentStatus.DONE.value
    db.commit()

    # TODO: it should be done when worker is here
    # settings = {}
    # db.add(schema.DocumentTask(document_id=new_doc.id, data=json.dumps(settings)))
    # db.commit()
    return StatusMessage(message="Ok")


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
def download_xliff(doc_id: int, db: Annotated[Session, Depends(get_db)]):
    doc = db.query(schema.XliffDocument).filter_by(id=doc_id).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    original_document = doc.original_document.encode("utf-8")
    processed_document = extract_xliff_content(original_document)

    for segment in processed_document.segments:
        record = db.query(schema.TmxRecord).filter_by(source=segment.original).first()
        if record:
            segment.translation = record.target

    processed_document.commit()
    file = processed_document.write()
    file.seek(0)
    return StreamingResponse(
        file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={doc.name}"},
    )
