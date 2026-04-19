import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.documents.models import Document, DocumentType
from app.formats.txt import extract_txt_content
from app.formats.xliff import extract_xliff_content
from app.glossary.models import GlossaryRecord
from app.translation_memory.models import TranslationMemoryRecord
from app.translation_memory.query import TranslationMemoryQuery
from worker.types import RecordSource, WorkerSegment


def extract_segments_from_file(doc: Document) -> Sequence[WorkerSegment]:
    if doc.type == DocumentType.xliff:
        xliff_document = doc.xliff
        xliff_data = extract_xliff_content(xliff_document.original_document.encode())
        return [
            WorkerSegment(type_="xliff", original_segment=segment)
            for segment in xliff_data.segments
        ]
    if doc.type == DocumentType.txt:
        txt_document = doc.txt
        txt_data = extract_txt_content(txt_document.original_document)
        return [
            WorkerSegment(type_="txt", original_segment=segment)
            for segment in txt_data.segments
        ]

    logging.error("Unknown document type")
    return []


def find_segment_translation(
    source: str,
    threshold: float,
    tm_ids: list[int],
    glossary_ids: list[int],
    session: Session,
) -> tuple[str, RecordSource | None] | None:
    # TODO: this would be nice to have batching for all segments to reduce amounts of requests to DB
    if source.isdigit():
        return source, RecordSource.full_match

    glossary_record = (
        session.query(GlossaryRecord)
        .where(
            GlossaryRecord.source == source,
            GlossaryRecord.glossary_id.in_(glossary_ids),
        )
        .first()
    )
    if glossary_record:
        return glossary_record.target, RecordSource.glossary

    if threshold < 1.0:
        substitutions = TranslationMemoryQuery(session).get_substitutions(
            source, tm_ids, threshold, 1
        )
        if substitutions:
            return substitutions[0].target, RecordSource.translation_memory
    else:
        selector = (
            select(TranslationMemoryRecord.source, TranslationMemoryRecord.target)
            .where(TranslationMemoryRecord.source == source)
            .where(TranslationMemoryRecord.document_id.in_(tm_ids))
            .order_by(TranslationMemoryRecord.change_date.desc())
        )
        tm_data = session.execute(selector.limit(1)).first()
        return (tm_data.target, RecordSource.translation_memory) if tm_data else None

    return None
