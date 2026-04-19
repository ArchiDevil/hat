# This is a worker that takes tasks from the database every N seconds and
# processes files in it.
# Tasks are stored in document_task table and encoded in JSON.

import json
import logging
import time
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentRecordHistory,
    DocumentRecordHistoryChangeType,
    DocumentType,
    TxtRecord,
    XliffRecord,
)
from app.documents.query import GenericDocsQuery
from app.documents.schema import DocumentProcessingSettings, DocumentTaskDescription
from app.formats.txt import TxtSegment
from app.formats.xliff import XliffSegment
from app.glossary.query import GlossaryQuery
from app.linguistic.word_count import count_words
from app.models import DocumentStatus, MachineTranslationSettings, TaskStatus
from app.schema import DocumentTask
from app.translators import llm, yandex
from app.translators.common import LineWithGlossaries
from worker.types import WorkerSegment
from worker.utils import (
    RecordSource,
    convert_segment_src,
    extract_segments_from_file,
    find_segment_translation,
)


def substitute_segments(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
    tm_ids: list[int],
    glossary_ids: list[int],
):
    # TODO: this is unsafe on LARGE files, consider doing it in pages
    empty_records = list(
        session.execute(
            select(DocumentRecord).where(
                DocumentRecord.document_id == doc.id,
                DocumentRecord.target == "",
                DocumentRecord.approved.is_(False),
            )
        )
        .scalars()
        .all()
    )
    history_records: list[DocumentRecordHistory] = []

    for record in empty_records:
        translation = find_segment_translation(
            source=record.source,
            threshold=settings.similarity_threshold,
            tm_ids=tm_ids,
            glossary_ids=glossary_ids,
            session=session,
        )

        if not translation:
            continue

        target_translation, segment_src = translation
        record.target = target_translation or ""

        # I hate it
        if segment_src == RecordSource.full_match:
            old_history = session.execute(
                select(DocumentRecordHistory).where(
                    DocumentRecordHistory.record_id == record.id,
                    DocumentRecordHistory.change_type
                    == DocumentRecordHistoryChangeType.initial_import.value,
                )
            ).scalar_one_or_none()
            if old_history:
                old_history.diff = json.dumps(
                    {"ops": [["insert", 0, 0, record.target]], "old_len": 0}
                )
                session.commit()
        else:
            history_records.append(
                DocumentRecordHistory(
                    record_id=record.id,
                    diff=json.dumps(
                        {"ops": [["insert", 0, 0, record.target]], "old_len": 0}
                    ),
                    change_type=convert_segment_src(segment_src),
                )
            )

        if segment_src in (RecordSource.full_match, RecordSource.glossary):
            record.approved = True

    # Create records history after update
    session.add_all(history_records)
    session.commit()


def translate_segments(
    doc: Document,
    glossary_ids: list[int],
    mt_settings: MachineTranslationSettings,
    session: Session,
) -> bool:
    mt_failed = False

    # TODO: this might be harmful with LLM translation as it is loses
    # the connectivity of the context
    # TODO: this is unsafe on LARGE files, consider doing it in pages
    empty_records = list(
        session.execute(
            select(DocumentRecord).where(
                DocumentRecord.document_id == doc.id,
                DocumentRecord.target == "",
                DocumentRecord.approved.is_(False),
            )
        )
        .scalars()
        .all()
    )
    history_records: list[DocumentRecordHistory] = []

    sentences_with_ctx: list[LineWithGlossaries] = []
    for record in empty_records:
        sentences_with_ctx.append(
            (
                record.source,
                [
                    (x.source, x.target)
                    for x in GlossaryQuery(session).get_glossary_records_for_phrase(
                        record.source, glossary_ids
                    )
                ],
            )
        )

    try:
        if mt_settings.type == "yandex":
            translated, mt_failed = yandex.translate_lines(
                sentences_with_ctx,
                oauth_token=mt_settings.oauth_token,
                folder_id=mt_settings.folder_id,
            )
        elif mt_settings.type == "llm":
            translated, mt_failed = llm.translate_lines(
                sentences_with_ctx, api_key=mt_settings.api_key
            )
        else:
            logging.fatal("Unknown translation API")
            raise RuntimeError("Unknown translation API")

        for idx, translated_line in enumerate(translated):
            empty_records[idx].target = translated_line
            history_records.append(
                DocumentRecordHistory(
                    record_id=empty_records[idx].id,
                    diff=json.dumps(
                        {
                            "ops": [["insert", 0, 0, empty_records[idx].target]],
                            "old_len": 0,
                        }
                    ),
                    change_type=DocumentRecordHistoryChangeType.machine_translation,
                )
            )

        session.add_all(history_records)
        session.commit()

    # TODO: handle specific exceptions instead of a generic one
    except Exception as e:
        logging.error("Machine translation error %s", e)
        return False

    return not mt_failed


def create_doc_segments(
    doc: Document,
    session: Session,
    segments: Sequence[WorkerSegment],
):
    # Create generic segments
    doc_records = [
        DocumentRecord(
            document_id=doc.id,
            source=segment.original_segment.original,
            target=segment.original_segment.translation or "",
            approved=segment.approved,
            word_count=count_words(segment.original_segment.original),
        )
        for segment in segments
    ]
    session.add_all(doc_records)
    session.commit()

    # Create initial history
    history_records: list[DocumentRecordHistory] = []
    for record in doc_records:
        history_records.append(
            DocumentRecordHistory(
                record_id=record.id,
                diff=json.dumps(
                    {"ops": [["insert", 0, 0, record.target]], "old_len": 0}
                ),
                change_type=DocumentRecordHistoryChangeType.initial_import,
            )
        )
    session.add_all(history_records)
    session.commit()

    # Create format specific segments
    if doc.type == DocumentType.xliff:
        xliff_records: Sequence[XliffRecord] = []
        for idx, segment in enumerate(segments):
            original = segment.original_segment
            assert isinstance(original, XliffSegment)
            if segment.approved:
                original.approved = True
            xliff_records.append(
                XliffRecord(
                    parent_id=doc_records[idx].id,
                    document_id=doc.xliff.id,
                    segment_id=original.id_,
                )
            )
        session.add_all(xliff_records)
    elif doc.type == DocumentType.txt:
        txt_records: Sequence[TxtRecord] = []
        for idx, segment in enumerate(segments):
            original = segment.original_segment
            assert isinstance(original, TxtSegment)
            txt_records.append(
                TxtRecord(
                    parent_id=doc_records[idx].id,
                    document_id=doc.txt.id,
                    offset=original.offset,
                )
            )
        session.add_all(txt_records)
    else:
        logging.error("Unsupported document type %s", doc.type)
    session.commit()


def process_document(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
) -> bool:
    # Phase 1: Extraction
    start_time = time.time()
    segments = extract_segments_from_file(doc)
    create_doc_segments(doc, session, segments)
    logging.info(
        "Segments extraction and creation time: %.2f seconds",
        time.time() - start_time,
    )

    # Phase 2: Substitution
    start_time = time.time()
    tm_ids = [x.id for x in doc.project.translation_memories]
    glossary_ids = [x.id for x in doc.project.glossaries]
    substitute_segments(doc, settings, session, tm_ids, glossary_ids)
    logging.info(
        "Segments substitution time: %.2f seconds",
        time.time() - start_time,
    )

    # Phase 3: Machine Translation
    start_time = time.time()
    mt_result = (
        translate_segments(
            doc,
            glossary_ids,
            settings.machine_translation_settings,
            session,
        )
        if settings.machine_translation_settings is not None
        else True
    )
    logging.info(
        "Machine translation time: %.2f seconds",
        time.time() - start_time,
    )

    return mt_result


def process_task(session: Session, task: DocumentTask) -> bool:
    start_time = time.time()
    doc: Document | None = None
    try:
        task.status = TaskStatus.PROCESSING.value
        session.commit()

        logging.info("New task found: %s", task.id)

        task_desc = DocumentTaskDescription.model_validate_json(task.data)
        task_data = task_desc.task_data

        if task_data.task_type != "document_processing":
            raise RuntimeError("Unable to handle task type", task_data.task_type)

        if task_data.document_type not in ["txt", "xliff"]:
            raise AttributeError("Task data 'type' field is not 'txt' or 'xliff'")

        doc = GenericDocsQuery(session).get_document(task_desc.document_id)

        if not doc:
            raise RuntimeError("Document not found")

        # TODO: what if the doc processing was started and left in a processing state?
        if doc.processing_status != DocumentStatus.PENDING.value:
            if doc.processing_status == DocumentStatus.PROCESSING.value:
                doc.processing_status = DocumentStatus.ERROR.value
                session.commit()
            raise RuntimeError("Document not in a pending state")

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
        if doc is not None:
            doc.processing_status = DocumentStatus.ERROR.value
            session.commit()
        return False
    finally:
        logging.info("Task finished %s, removing...", task.id)
        logging.info("Task took %.2f seconds", time.time() - start_time)
        session.delete(task)
        session.commit()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
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
