from datetime import datetime, timedelta
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import schema, models
from app.db import get_db
from app.xliff import extract_xliff_content

# TODO: add XLIFF segments statuses according to the specification
# TODO: understand how to create docker image for the worker process
# TODO: understand how to debug everything as a whole system


router = APIRouter(prefix="/xliff", tags=["xliff"])


@router.get("/")
def get_xliffs(db: Annotated[Session, Depends(get_db)]) -> list[models.XliffFile]:
    xliffs = (
        db.query(schema.XliffDocument)
        .filter(schema.XliffDocument.processing_status != "uploaded")
        .order_by(schema.XliffDocument.id)
        .all()
    )
    return [
        models.XliffFile(
            id=xliff.id,
            name=xliff.name,
            status=models.DocumentStatus(xliff.processing_status),
        )
        for xliff in xliffs
    ]


@router.get("/{doc_id}")
def get_xliff(doc_id: int, db: Annotated[Session, Depends(get_db)]) -> models.XliffFile:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return models.XliffFile(
        id=doc.id,
        name=doc.name,
        status=models.DocumentStatus(doc.processing_status),
    )


@router.get("/{doc_id}/records")
def get_xliff_records(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[models.XliffFileRecord]:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return [
        models.XliffFileRecord(
            id=record.id,
            segment_id=record.segment_id,
            source=record.source,
            target=record.target,
        )
        for record in doc.records
    ]


@router.delete("/{doc_id}")
def delete_xliff(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    db.delete(doc)
    db.commit()
    return models.StatusMessage(message="Deleted")


@router.post("/")
async def create_xliff(
    file: Annotated[UploadFile, File()], db: Annotated[Session, Depends(get_db)]
) -> models.XliffFile:
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
        processing_status=models.DocumentStatus.UPLOADED.value,
        upload_time=datetime.now(),
    )
    db.add(doc)
    db.commit()

    new_doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc.id).one()
    )
    return models.XliffFile(
        id=new_doc.id,
        name=new_doc.name,
        status=models.DocumentStatus(new_doc.processing_status),
    )


@router.post("/{doc_id}/process")
def process_xliff(
    doc_id: int,
    settings: models.XliffProcessingSettings,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    doc = db.query(schema.XliffDocument).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    doc.processing_status = models.DocumentStatus.PENDING.value
    db.commit()

    task_config = {
        "type": "xliff",
        "doc_id": doc_id,
        "settings": settings.model_dump_json(),
    }
    db.add(
        schema.DocumentTask(
            data=json.dumps(task_config), status=models.TaskStatus.PENDING.value
        )
    )
    db.commit()
    return models.StatusMessage(message="Ok")


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
