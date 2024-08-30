# This is a worker that takes tasks from the database every 10 seconds and
# processes files in it.
# Tasks are stored in document_task table and encoded in JSON.

import logging
import time
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentType,
    TxtRecord,
    XliffRecord,
)
from app.documents.query import GenericDocsQuery
from app.documents.schema import DocumentProcessingSettings, DocumentTaskDescription
from app.formats.base import BaseSegment
from app.formats.txt import TxtSegment, extract_txt_content
from app.formats.xliff import XliffSegment, extract_xliff_content
from app.models import DocumentStatus, MachineTranslationSettings, TaskStatus
from app.schema import DocumentTask
from app.translation_memory.models import TranslationMemoryRecord
from app.translation_memory.query import TranslationMemoryQuery
from app.translation_memory.schema import TranslationMemoryUsage
from app.translators import yandex


def segment_needs_processing(segment: BaseSegment) -> bool:
    if isinstance(segment, XliffSegment):
        return not segment.approved
    return True


def get_segment_translation(
    source: str,
    threshold: float,
    tm_ids: list[int],
    tm_usage: TranslationMemoryUsage,
    substitute_numbers: bool,
    session: Session,
) -> str | None:
    # TODO: this would be nice to have batching for all segments to reduce amounts of requests to DB
    if substitute_numbers and source.isdigit():
        return source

    if threshold < 1.0:
        substitutions = TranslationMemoryQuery(session).get_substitutions(
            source, tm_ids, threshold, 1
        )
        if substitutions:
            return substitutions[0].target
    else:
        selector = (
            select(TranslationMemoryRecord.source, TranslationMemoryRecord.target)
            .where(TranslationMemoryRecord.source == source)
            .where(TranslationMemoryRecord.document_id.in_(tm_ids))
        )
        match tm_usage:
            case TranslationMemoryUsage.NEWEST:
                selector = selector.order_by(TranslationMemoryRecord.change_date.desc())
            case TranslationMemoryUsage.OLDEST:
                selector = selector.order_by(TranslationMemoryRecord.change_date.asc())
            case _:
                logging.error("Unknown translation memory usage option")
                return None

        tm_data = session.execute(selector.limit(1)).first()
        return tm_data.target if tm_data else None

    return None


def process_document(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
) -> bool:
    start_time = time.time()
    segments = extract_segments(doc)
    logging.info(
        "Segments extraction time: %.2f seconds, speed: %.2f segment/second",
        time.time() - start_time,
        len(segments) / (time.time() - start_time + 0.01),
    )

    start_time = time.time()
    translate_indices = substitute_segments(settings, session, segments)
    logging.info(
        "Segments substitution time: %.2f seconds, speed: %.2f segment/second, segments: %d/%d",
        time.time() - start_time,
        (len(translate_indices)) / (time.time() - start_time + 0.01),
        len(translate_indices),
        len(segments),
    )

    start_time = time.time()
    mt_result = translate_segments(
        segments, translate_indices, settings.machine_translation_settings
    )
    logging.info(
        "Machine translation time: %.2f seconds, speed: %.2f segment/second, segments: %d/%d",
        time.time() - start_time,
        (len(segments) - len(translate_indices)) / (time.time() - start_time + 0.01),
        len(segments) - len(translate_indices),
        len(segments),
    )

    start_time = time.time()
    create_doc_segments(doc, session, segments)
    logging.info(
        "Database segments creation time: %.2f seconds, speed: %.2f segment/second",
        time.time() - start_time,
        len(segments) / (time.time() - start_time + 0.01),
    )

    return mt_result


def extract_segments(doc: Document) -> Sequence[BaseSegment]:
    if doc.type == DocumentType.xliff:
        xliff_document = doc.xliff
        xliff_data = extract_xliff_content(xliff_document.original_document.encode())
        return xliff_data.segments
    if doc.type == DocumentType.txt:
        txt_document = doc.txt
        txt_data = extract_txt_content(txt_document.original_document)
        return txt_data.segments

    logging.error("Unknown document type")
    return []


def substitute_segments(
    settings: DocumentProcessingSettings,
    session: Session,
    segments: Iterable[BaseSegment],
) -> list[int]:
    """
    Process what is possible to process, save segment indices for further machine
    translation processing.
    """
    to_translate: list[int] = []
    for idx, segment in enumerate(segments):
        if not segment_needs_processing(segment):
            continue

        translation = get_segment_translation(
            segment.original,
            settings.similarity_threshold,
            settings.memory_ids,
            settings.memory_usage,
            settings.substitute_numbers,
            session,
        )
        if not translation:
            to_translate.append(idx)
            continue

        segment.translation = translation or ""
    return to_translate


def translate_segments(
    segments: Sequence[BaseSegment],
    translate_indices: Sequence[int],
    mt_settings: MachineTranslationSettings | None,
) -> bool:
    # TODO: it is better to make solution more translation service agnostic
    mt_failed = False
    if mt_settings and translate_indices:
        try:
            lines = [segments[idx].original for idx in translate_indices]
            translated, mt_failed = yandex.translate_lines(
                [(line, []) for line in lines],
                oauth_token=mt_settings.oauth_token,
                folder_id=mt_settings.folder_id,
            )
            for idx, translated_line in enumerate(translated):
                segments[translate_indices[idx]].translation = translated_line
        # TODO: handle specific exceptions instead of a generic one
        except Exception as e:
            logging.error("Yandex translation error %s", e)
            return False
    return not mt_failed


def create_doc_segments(
    doc: Document,
    session: Session,
    segments: Iterable[BaseSegment],
) -> None:
    doc_records = [
        DocumentRecord(
            document_id=doc.id,
            source=segment.original,
            target=segment.translation or "",
        )
        for segment in segments
    ]
    session.add_all(doc_records)
    session.commit()

    # create document specific segments
    # TODO: is this possible to make it better?
    if doc.type == DocumentType.xliff:
        xliff_records: Sequence[XliffRecord] = []
        for idx, segment in enumerate(segments):
            assert isinstance(segment, XliffSegment)
            xliff_records.append(
                XliffRecord(
                    parent_id=doc_records[idx].id,
                    document_id=doc.xliff.id,
                    segment_id=segment.id_,
                    state=segment.state.value,
                    approved=segment.approved,
                )
            )
        session.add_all(xliff_records)
        session.commit()
    elif doc.type == DocumentType.txt:
        txt_records: Sequence[TxtRecord] = []
        for idx, segment in enumerate(segments):
            assert isinstance(segment, TxtSegment)
            txt_records.append(
                TxtRecord(
                    parent_id=doc_records[idx].id,
                    document_id=doc.txt.id,
                    offset=segment.offset,
                )
            )
        session.add_all(txt_records)
        session.commit()
    else:
        logging.error("Unsupported document type %s", doc.type)


def process_task(session: Session, task: DocumentTask) -> bool:
    start_time = time.time()
    try:
        task.status = TaskStatus.PROCESSING.value
        session.commit()

        logging.info("New task found: %s", task.id)

        task_data = DocumentTaskDescription.model_validate_json(task.data)

        if task_data.type not in ["txt", "xliff"]:
            logging.error("Task data 'type' field is not 'txt' or 'xliff'")
            raise AttributeError("Task data 'type' field is not 'txt' or 'xliff'")

        doc = GenericDocsQuery(session).get_document(task_data.document_id)

        # TODO: what if the doc processing was started and left in a processing state?
        if not doc or doc.processing_status != DocumentStatus.PENDING.value:
            logging.error("Document not found or not in a pending state")
            return False

        doc.processing_status = DocumentStatus.PROCESSING.value
        session.commit()

        if not process_document(doc, task_data.settings, session):
            doc.processing_status = DocumentStatus.ERROR.value
            session.commit()
            logging.error("Processing failed for document %d", doc.id)
            return False

        doc.processing_status = DocumentStatus.DONE.value
        session.commit()
        return True
    except Exception as e:
        logging.error("Task processing failed: %s", str(e))
        return False
    finally:
        logging.info("Task finished %s, removing...", task.id)
        logging.info("Task took %.2f seconds", time.time() - start_time)
        session.delete(task)
        session.commit()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Starting document processing")

    session = next(get_db())
    while True:
        task = session.query(DocumentTask).first()
        if not task:
            time.sleep(10)
            continue

        process_task(session, task)


if __name__ == "__main__":
    main()
