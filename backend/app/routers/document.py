from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schema
from app.db import get_db
from app.documents import schema as doc_schema
from app.documents.models import (
    Document,
    DocumentType,
    XliffRecord,
)
from app.documents.query import GenericDocsQuery
from app.formats.txt import extract_txt_content
from app.formats.xliff import SegmentState, extract_xliff_content
from app.translation_memory.schema import MemorySubstitution
from app.translation_memory.utils import get_substitutions
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/document", tags=["document"], dependencies=[Depends(has_user_role)]
)


def get_doc_by_id(db: Session, document_id: int) -> Document:
    doc = GenericDocsQuery(db).get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/")
def get_docs(db: Annotated[Session, Depends(get_db)]) -> list[doc_schema.Document]:
    docs = GenericDocsQuery(db).get_documents_list()
    return [
        doc_schema.Document(
            id=doc.id,
            name=doc.name,
            status=models.DocumentStatus(doc.processing_status),
            created_by=doc.created_by,
        )
        for doc in docs
    ]


@router.get("/{doc_id}")
def get_doc(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> doc_schema.DocumentWithRecordsCount:
    doc = get_doc_by_id(db, doc_id)
    records_count = len(list(GenericDocsQuery(db).get_document_records(doc)))
    return doc_schema.DocumentWithRecordsCount(
        id=doc.id,
        name=doc.name,
        status=models.DocumentStatus(doc.processing_status),
        created_by=doc.created_by,
        records_count=records_count,
    )


@router.get("/{doc_id}/records")
def get_doc_records(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
) -> list[doc_schema.DocumentRecord]:
    if not page:
        page = 0

    doc = get_doc_by_id(db, doc_id)
    records = GenericDocsQuery(db).get_document_records_paged(doc, page)
    return [
        doc_schema.DocumentRecord(
            id=record.id,
            source=record.source,
            target=record.target,
        )
        for record in records
    ]


@router.get("/{doc_id}/segments/{segment_id}/substitutions")
def get_segment_substitutions(
    doc_id: int, segment_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[MemorySubstitution]:
    doc = get_doc_by_id(db, doc_id)
    original_segment = GenericDocsQuery(db).get_record(doc_id, segment_id)
    if not original_segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found"
        )

    tmx_ids = [tmx.id for tmx in doc.tmxs]
    if not tmx_ids:
        return []

    return get_substitutions(original_segment.source, tmx_ids, db)


@router.put("/{doc_id}/record/{record_id}")
def update_doc_record(
    doc_id: int,
    record_id: int,
    record: doc_schema.DocumentRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    # to check if doc exists
    get_doc_by_id(db, doc_id)
    found_record = GenericDocsQuery(db).get_record(doc_id, record_id)
    if not found_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        )

    GenericDocsQuery(db).update_record_target(found_record, record.target)
    return models.StatusMessage(message="Record updated")


@router.delete("/{doc_id}")
def delete_doc(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    GenericDocsQuery(db).delete_document(get_doc_by_id(db, doc_id))
    return models.StatusMessage(message="Deleted")


@router.post("/")
async def create_doc(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> doc_schema.Document:
    # Create an XLIFF file and upload it to the server
    cutoff_date = datetime.now() - timedelta(days=1)

    # Remove outdated files when adding a new one
    query = GenericDocsQuery(db)
    outdated_docs = query.get_outdated_documents(cutoff_date)
    query.bulk_delete_documents(outdated_docs)

    name = str(file.filename)
    file_data = await file.read()
    original_document = file_data.decode("utf-8")

    # quite simple logic, but it is fine for now
    ext = name.lower().split(".")[-1]
    if ext == "xliff":
        doc_type = DocumentType.xliff
    elif ext == "txt":
        doc_type = DocumentType.txt
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type"
        )

    doc = Document(
        name=name,
        type=doc_type,
        processing_status=models.DocumentStatus.UPLOADED.value,
        upload_time=datetime.now(),
        created_by=current_user,
    )
    query.add_document(doc, original_document)
    return doc_schema.Document(
        id=doc.id,
        name=doc.name,
        status=models.DocumentStatus(doc.processing_status),
        created_by=doc.created_by,
    )


@router.post("/{doc_id}/process")
def process_doc(
    doc_id: int,
    settings: doc_schema.DocumentProcessingSettings,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    doc = get_doc_by_id(db, doc_id)
    GenericDocsQuery(db).enqueue_document(doc, settings.tmx_file_ids)

    task_config = doc_schema.DocumentTaskDescription(
        type=doc.type.value, document_id=doc_id, settings=settings
    )
    db.add(
        schema.DocumentTask(
            data=task_config.model_dump_json(), status=models.TaskStatus.PENDING.value
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
def download_doc(doc_id: int, db: Annotated[Session, Depends(get_db)]):
    def encode_to_latin_1(original: str):
        output = ""
        for c in original:
            output += c if (c.isalnum() or c in "'().[] -") else "_"
        return output

    doc = get_doc_by_id(db, doc_id)
    if doc.type == DocumentType.xliff:
        if not doc.xliff:
            raise HTTPException(status_code=404, detail="No XLIFF file found")

        original_document = doc.xliff.original_document.encode("utf-8")
        processed_document = extract_xliff_content(original_document)

        for segment in processed_document.segments:
            record = db.query(XliffRecord).filter_by(segment_id=segment.id_).first()
            if record and not segment.approved:
                segment.translation = record.parent.target
                segment.approved = record.approved
                segment.state = SegmentState(record.state)

        processed_document.commit()
        file = processed_document.write()
        return StreamingResponse(
            file,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
            },
        )

    if doc.type == DocumentType.txt:
        if not doc.txt:
            raise HTTPException(status_code=404, detail="No TXT file found")

        original_document = doc.txt.original_document
        processed_document = extract_txt_content(original_document)

        txt_records = doc.txt.records
        for i, segment in enumerate(processed_document.segments):
            record = txt_records[i]
            if record:
                segment.translation = record.parent.target

        processed_document.commit()
        file = processed_document.write()
        return StreamingResponse(
            file,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{encode_to_latin_1(doc.name)}"'
            },
        )

    raise HTTPException(status_code=404, detail="Unknown document type")
