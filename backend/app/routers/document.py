from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schema
from app.comments.query import CommentsQuery
from app.comments.schema import CommentCreate, CommentResponse
from app.db import get_db
from app.documents import schema as doc_schema
from app.documents.models import (
    Document,
    DocumentType,
    TmMode,
    XliffRecord,
)
from app.documents.query import GenericDocsQuery, NotFoundDocumentRecordExc
from app.formats.txt import extract_txt_content
from app.formats.xliff import SegmentState, extract_xliff_content
from app.glossary.query import GlossaryQuery, NotFoundGlossaryExc
from app.glossary.schema import GlossaryRecordSchema, GlossaryResponse
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import (
    MemorySubstitution,
    TranslationMemory,
    TranslationMemoryListResponse,
    TranslationMemoryListSimilarResponse,
)
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/document", tags=["document"], dependencies=[Depends(has_user_role)]
)


def get_doc_by_id(db: Session, document_id: int) -> Document:
    doc = GenericDocsQuery(db).get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def get_doc_record_by_id(db: Session, record_id: int):
    """Helper function to get document record by ID"""
    record = GenericDocsQuery(db).get_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found"
        )
    return record


@router.get("/")
def get_docs(
    db: Annotated[Session, Depends(get_db)],
) -> list[doc_schema.DocumentWithRecordsCount]:
    query = GenericDocsQuery(db)
    docs = query.get_documents_list()
    output = []
    for doc in docs:
        records = query.get_document_records_count_with_approved(doc)
        words = query.get_document_word_count_with_approved(doc)
        output.append(
            doc_schema.DocumentWithRecordsCount(
                id=doc.id,
                name=doc.name,
                status=models.DocumentStatus(doc.processing_status),
                created_by=doc.created_by,
                type=doc.type.value,
                approved_records_count=records[0],
                records_count=records[1],
                approved_word_count=words[0],
                total_word_count=words[1],
            )
        )
    return output


@router.get("/{doc_id}")
def get_doc(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> doc_schema.DocumentWithRecordsCount:
    doc = get_doc_by_id(db, doc_id)
    query = GenericDocsQuery(db)
    records = query.get_document_records_count_with_approved(doc)
    words = query.get_document_word_count_with_approved(doc)
    return doc_schema.DocumentWithRecordsCount(
        id=doc.id,
        name=doc.name,
        status=models.DocumentStatus(doc.processing_status),
        created_by=doc.created_by,
        type=doc.type.value,
        approved_records_count=records[0],
        records_count=records[1],
        approved_word_count=words[0],
        total_word_count=words[1],
    )


@router.get("/{doc_id}/records")
def get_doc_records(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int | None, Query(ge=0)] = None,
    source: Annotated[
        str | None, Query(description="Filter by source text (contains search)")
    ] = None,
    target: Annotated[
        str | None, Query(description="Filter by target text (contains search)")
    ] = None,
) -> doc_schema.DocumentRecordListResponse:
    if not page:
        page = 0

    filters = None
    if source or target:
        filters = doc_schema.DocumentRecordFilter(
            source_filter=source, target_filter=target
        )

    doc = get_doc_by_id(db, doc_id)
    query = GenericDocsQuery(db)
    total_records = query.get_document_records_count_filtered(doc, filters)
    records = query.get_document_records_paged(doc, page, filters=filters)
    record_list = [
        doc_schema.DocumentRecord(
            id=record.id,
            source=record.source,
            target=record.target,
            approved=record.approved,
            repetitions_count=repetitions_count,
            has_comments=has_comments,
            translation_src=(
                record.target_source.value if record.target_source else None
            ),
        )
        for record, repetitions_count, has_comments in records
    ]

    return doc_schema.DocumentRecordListResponse(
        records=record_list,
        page=page,
        total_records=total_records,
    )


@router.get("/{doc_id}/glossary_search")
def doc_glossary_search(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query()],
) -> list[GlossaryRecordSchema]:
    doc = get_doc_by_id(db, doc_id)
    glossary_ids = [gl.id for gl in doc.glossaries]
    return (
        [
            GlossaryRecordSchema.model_validate(record)
            for record in GlossaryQuery(db).get_glossary_records_for_phrase(
                query, glossary_ids
            )
        ]
        if glossary_ids
        else []
    )


@router.get("/records/{record_id}/comments")
def get_comments(
    record_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> list[CommentResponse]:
    """Get all comments for a document record"""
    # Verify document record exists
    get_doc_record_by_id(db, record_id)

    comments = CommentsQuery(db).get_comments_by_document_record(record_id)
    return [CommentResponse.model_validate(comment) for comment in comments]


@router.post("/records/{record_id}/comments")
def create_comment(
    record_id: int,
    comment_data: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> CommentResponse:
    """Create a new comment for a document record"""
    # Verify document record exists
    get_doc_record_by_id(db, record_id)

    comment = CommentsQuery(db).create_comment(comment_data, current_user, record_id)
    return CommentResponse.model_validate(comment)


@router.get("/records/{record_id}/substitutions")
def get_record_substitutions(
    record_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[MemorySubstitution]:
    original_segment = GenericDocsQuery(db).get_record(record_id)
    if not original_segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found"
        )

    tm_ids = [tm.id for tm in original_segment.document.memories]
    return (
        TranslationMemoryQuery(db).get_substitutions(original_segment.source, tm_ids)
        if tm_ids
        else []
    )


@router.get("/records/{record_id}/glossary_records")
def get_record_glossary_records(
    record_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[GlossaryRecordSchema]:
    original_segment = GenericDocsQuery(db).get_record(record_id)
    if not original_segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found"
        )

    glossary_ids = [gl.id for gl in original_segment.document.glossaries]
    return (
        [
            GlossaryRecordSchema.model_validate(record)
            for record in GlossaryQuery(db).get_glossary_records_for_phrase(
                original_segment.source, glossary_ids
            )
        ]
        if glossary_ids
        else []
    )


@router.put("/records/{record_id}")
def update_doc_record(
    record_id: int,
    record: doc_schema.DocumentRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> doc_schema.DocumentRecordUpdateResponse:
    try:
        updated_record = GenericDocsQuery(db).update_record(record_id, record)
        return doc_schema.DocumentRecordUpdateResponse(
            id=updated_record.id,
            source=updated_record.source,
            target=updated_record.target,
            approved=updated_record.approved,
        )
    except NotFoundDocumentRecordExc as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        ) from e


@router.get("/{doc_id}/memories")
def get_translation_memories(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[doc_schema.DocTranslationMemory]:
    return [
        doc_schema.DocTranslationMemory(
            document_id=doc_id,
            memory=TranslationMemory(
                id=association.memory.id,
                name=association.memory.name,
                created_by=association.memory.created_by,
            ),
            mode=association.mode,
        )
        for association in get_doc_by_id(db, doc_id).memory_associations
    ]


@router.post("/{doc_id}/memories")
def set_translation_memories(
    doc_id: int,
    settings: doc_schema.DocTranslationMemoryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    # check writes count
    write_count = 0
    for memory in settings.memories:
        write_count += memory.mode == TmMode.write

    if write_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not all memories were found",
        )

    # check that all memories are available
    doc = get_doc_by_id(db, doc_id)
    memory_ids = {memory.id for memory in settings.memories}
    memories = list(TranslationMemoryQuery(db).get_memories_by_id(memory_ids))
    if len(memory_ids) != len(memories):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not all memories were found",
        )

    def find_memory(id_: int, memories):
        for memory in memories:
            if memory.id == id_:
                return memory
        return None

    mem_to_mode = [
        (find_memory(memory.id, memories), memory.mode) for memory in settings.memories
    ]
    GenericDocsQuery(db).set_document_memories(doc, mem_to_mode)
    return models.StatusMessage(message="Memory list updated")


@router.get("/{doc_id}/tm/exact")
def search_tm_exact(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListResponse:
    doc = get_doc_by_id(db, doc_id)
    tm_ids = [tm.id for tm in doc.memories]

    if not tm_ids:
        return TranslationMemoryListResponse(records=[], page=0, total_records=0)

    records, count = TranslationMemoryQuery(db).get_memory_records_paged(
        memory_ids=tm_ids,
        page=0,
        page_records=20,
        query=source,
    )

    return TranslationMemoryListResponse(
        records=records,
        page=0,
        total_records=count,
    )


@router.get("/{doc_id}/tm/similar")
def search_tm_similar(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
    source: Annotated[str, Query(description="Source text to search for")],
) -> TranslationMemoryListSimilarResponse:
    doc = get_doc_by_id(db, doc_id)
    tm_ids = [tm.id for tm in doc.memories]

    if not tm_ids:
        return TranslationMemoryListSimilarResponse(records=[], page=0, total_records=0)

    records = TranslationMemoryQuery(db).get_memory_records_paged_similar(
        memory_ids=tm_ids,
        page_records=20,
        query=source,
    )

    return TranslationMemoryListSimilarResponse(
        records=records,
        page=0,
        total_records=len(records),
    )


@router.get("/{doc_id}/glossaries")
def get_glossaries(
    doc_id: int, db: Annotated[Session, Depends(get_db)]
) -> list[doc_schema.DocGlossary]:
    doc = get_doc_by_id(db, doc_id)
    return [
        doc_schema.DocGlossary(
            document_id=doc.id,
            glossary=GlossaryResponse.model_validate(x.glossary),
        )
        for x in doc.glossary_associations
    ]


@router.post("/{doc_id}/glossaries")
def set_glossaries(
    doc_id: int,
    settings: doc_schema.DocGlossaryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    # check that all glossaries exist
    doc = get_doc_by_id(db, doc_id)
    glossary_ids = {g.id for g in settings.glossaries}
    try:
        glossaries = list(GlossaryQuery(db).get_glossaries(list(glossary_ids)))
    except NotFoundGlossaryExc as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Glossary not found"
        ) from exc

    if len(glossary_ids) != len(glossaries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not all glossaries were found",
        )
    GenericDocsQuery(db).set_document_glossaries(doc, glossaries)
    return models.StatusMessage(message="Glossary list updated")


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
        type=doc.type.value,
    )


@router.post("/{doc_id}/process")
def process_doc(
    doc_id: int,
    settings: doc_schema.DocumentProcessingSettings,
    db: Annotated[Session, Depends(get_db)],
) -> models.StatusMessage:
    doc = get_doc_by_id(db, doc_id)
    GenericDocsQuery(db).enqueue_document(doc)

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
                segment.approved = record.parent.approved
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
