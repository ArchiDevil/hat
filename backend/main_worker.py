# This is a worker that takes tasks from the database every N seconds and
# processes files in it.
# Tasks are stored in document_task table and encoded in JSON.

import json
import logging
import time
from typing import Iterable, Sequence

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
    extract_segments_from_file,
    find_segment_translation,
)


def substitute_segments(
    settings: DocumentProcessingSettings,
    session: Session,
    segments: Iterable[WorkerSegment],
    tm_ids: list[int],
    glossary_ids: list[int],
) -> list[int]:
    """
    Process what is possible to process, save segment indices for further machine
    translation processing.
    """
    to_translate: list[int] = []
    for idx, segment in enumerate(segments):
        if not segment.needs_processing:
            continue

        translation = find_segment_translation(
            source=segment.original_segment.original,
            threshold=settings.similarity_threshold,
            tm_ids=tm_ids,
            glossary_ids=glossary_ids,
            session=session,
        )
        if not translation:
            to_translate.append(idx)
            continue

        target_translation, segment_src = translation
        segment.original_segment.translation = target_translation or ""
        segment.segment_source = segment_src
        if segment_src in (RecordSource.full_match, RecordSource.glossary):
            segment.approved = True
    return to_translate


def translate_segments(
    segments: Sequence[WorkerSegment],
    translate_indices: Sequence[int],
    glossary_ids: list[int],
    mt_settings: MachineTranslationSettings,
    session: Session,
) -> bool:
    if not translate_indices:
        return True

    mt_failed = False
    try:
        # TODO: this might be harmful with LLM translation as it is loses
        # the connectivity of the context
        segments_to_translate = [
            segments[idx].original_segment.original for idx in translate_indices
        ]
        data_to_translate: list[LineWithGlossaries] = []
        for segment in segments_to_translate:
            glossary_records = GlossaryQuery(session).get_glossary_records_for_phrase(
                segment, glossary_ids
            )
            data_to_translate.append(
                (segment, [(x.source, x.target) for x in glossary_records])
            )
        if mt_settings.type == "yandex":
            translated, mt_failed = yandex.translate_lines(
                data_to_translate,
                oauth_token=mt_settings.oauth_token,
                folder_id=mt_settings.folder_id,
            )
        elif mt_settings.type == "llm":
            translated, mt_failed = llm.translate_lines(
                data_to_translate, api_key=mt_settings.api_key
            )
        else:
            logging.fatal("Unknown translation API")
            raise RuntimeError("Unknown translation API")
        for idx, translated_line in enumerate(translated):
            segments[
                translate_indices[idx]
            ].original_segment.translation = translated_line
    # TODO: handle specific exceptions instead of a generic one
    except Exception as e:
        logging.error("Machine translation error %s", e)
        return False

    return not mt_failed


def create_doc_segments(
    doc: Document,
    session: Session,
    segments: Sequence[WorkerSegment],
) -> None:
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

    def convert_segment_src(
        src: RecordSource | None,
    ) -> DocumentRecordHistoryChangeType:
        if src == RecordSource.glossary:
            return DocumentRecordHistoryChangeType.glossary_substitution
        elif src == RecordSource.machine_translation:
            return DocumentRecordHistoryChangeType.machine_translation
        elif src == RecordSource.translation_memory:
            return DocumentRecordHistoryChangeType.tm_substitution
        else:
            return DocumentRecordHistoryChangeType.initial_import

    history_records = [
        DocumentRecordHistory(
            record_id=record.id,
            diff=json.dumps({"ops": [["insert", 0, 0, record.target]], "old_len": 0}),
            change_type=convert_segment_src(segments[i].segment_source),
        )
        for i, record in enumerate(doc_records)
    ]
    session.add_all(history_records)
    session.commit()

    # create document specific segments
    # TODO: is this possible to make it better?
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
                    state=original.state.value,
                )
            )
        session.add_all(xliff_records)
        session.commit()
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
        session.commit()
    else:
        logging.error("Unsupported document type %s", doc.type)


def process_document(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
) -> bool:
    start_time = time.time()
    segments = extract_segments_from_file(doc)
    logging.info(
        "Segments extraction time: %.2f seconds, speed: %.2f segment/second",
        time.time() - start_time,
        len(segments) / (time.time() - start_time + 0.01),
    )

    tm_ids = [x.id for x in doc.project.translation_memories]
    glossary_ids = [x.id for x in doc.project.glossaries]

    start_time = time.time()
    translate_indices = substitute_segments(
        settings, session, segments, tm_ids, glossary_ids
    )
    logging.info(
        "Segments substitution time: %.2f seconds, speed: %.2f segment/second, segments: %d/%d",
        time.time() - start_time,
        (len(segments) - len(translate_indices)) / (time.time() - start_time + 0.01),
        len(segments) - len(translate_indices),
        len(segments),
    )

    start_time = time.time()
    mt_result = (
        translate_segments(
            segments,
            translate_indices,
            glossary_ids,
            settings.machine_translation_settings,
            session,
        )
        if settings.machine_translation_settings is not None
        else True
    )
    logging.info(
        "Machine translation time: %.2f seconds, speed: %.2f segment/second, segments: %d/%d",
        time.time() - start_time,
        (len(translate_indices)) / (time.time() - start_time + 0.01),
        len(translate_indices),
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


def process_task(session: Session, task: DocumentTask) -> bool:
    start_time = time.time()
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

        # TODO: what if the doc processing was started and left in a processing state?
        if not doc or doc.processing_status != DocumentStatus.PENDING.value:
            raise RuntimeError("Document not found or not in a pending state")

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
