import json
from datetime import datetime, timedelta
from typing import Annotated, Final

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app import models, schema
from app.auth import get_current_user_id, has_user_role
from app.db import get_db
from app.xliff import SegmentState, extract_xliff_content

# TODO: add XLIFF segments statuses according to the specification


router = APIRouter(
    prefix="/xliff", tags=["xliff"], dependencies=[Depends(has_user_role)]
)


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
            created_by=xliff.created_by,
        )
        for xliff in xliffs
    ]


@router.get("/{doc_id}")
def get_xliff(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.XliffFileWithRecordsCount:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records_count = (
        db.query(schema.XliffRecord).filter(schema.XliffRecord.document == doc).count()
    )

    return models.XliffFileWithRecordsCount(
        id=doc.id,
        name=doc.name,
        status=models.DocumentStatus(doc.processing_status),
        created_by=doc.created_by,
        records_count=records_count,
    )


@router.get("/{doc_id}/records")
def get_xliff_records(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[models.XliffFileRecord]:
    page_records: Final = 100
    if not page:
        page = 0

    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    records = (
        db.query(schema.XliffRecord)
        .filter(schema.XliffRecord.document_id == doc_id)
        .order_by(schema.XliffRecord.segment_id)
        .offset(page_records * page)
        .limit(page_records)
        .all()
    )

    return [
        models.XliffFileRecord(
            id=record.id,
            segment_id=record.segment_id,
            source=record.source,
            target=record.target,
            state=record.state,
            approved=record.approved,
        )
        for record in records
    ]


@router.get("/{doc_id}/segments/{segment_id}/substitutions")
def get_segment_substitutions(
    doc_id: int, segment_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[models.XliffSubstitution]:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    original_segment = (
        db.query(schema.XliffRecord).filter(schema.XliffRecord.id == segment_id).first()
    )
    if not original_segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found"
        )

    tmx_ids = [tmx.id for tmx in doc.tmxs]
    if not tmx_ids:
        return []

    similarity_func = func.similarity(schema.TmxRecord.source, original_segment.source)
    db.execute(
        text("SET pg_trgm.similarity_threshold TO :threshold"), {"threshold": 0.7}
    )
    records = db.execute(
        select(schema.TmxRecord.source, schema.TmxRecord.target, similarity_func)
        .filter(
            schema.TmxRecord.source.op("%")(original_segment.source),
            schema.TmxRecord.id.in_(tmx_ids),
        )
        .order_by(similarity_func.desc())
        .limit(10),
    ).all()

    return [
        models.XliffSubstitution(source=source, target=target, similarity=similarity)
        for (source, target, similarity) in records
    ]


@router.put("/{doc_id}/record/{record_id}")
def update_xliff_record(
    doc_id: int,
    record_id: int,
    record: models.XliffRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    doc = (
        db.query(schema.XliffDocument).filter(schema.XliffDocument.id == doc_id).first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    found_record = (
        db.query(schema.XliffRecord)
        .filter(schema.XliffRecord.document_id == doc_id)
        .filter(schema.XliffRecord.id == record_id)
        .first()
    )
    if not found_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        )

    found_record.target = record.target
    db.commit()

    return models.StatusMessage(message="Record updated")


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
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
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
        created_by=current_user,
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
        created_by=new_doc.created_by,
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
    tmxs = (
        db.query(schema.TmxDocument)
        .filter(schema.TmxDocument.id.in_(settings.tmx_file_ids))
        .all()
    )
    doc.tmxs = tmxs
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
        record = db.query(schema.XliffRecord).filter_by(segment_id=segment.id_).first()
        if record and not segment.approved:
            segment.translation = record.target
            segment.approved = record.approved
            segment.state = SegmentState(record.state)

    def encode_to_latin_1(original: str):
        output = ""
        for c in original:
            output += c if (c.isalnum() or c in "'().[] -") else "_"
        return output

    processed_document.commit()
    file = processed_document.write()
    file.seek(0)
    return StreamingResponse(
        file,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
        },
    )
