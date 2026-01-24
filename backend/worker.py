# This is a worker that takes tasks from the database every N seconds and
# processes files in it.
# Tasks are stored in document_task table and encoded in JSON.

import json
import logging
import time
from enum import Enum
from typing import Iterable, Literal, Sequence, overload

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
from app.formats.txt import TxtSegment, extract_txt_content
from app.formats.xliff import XliffSegment, extract_xliff_content
from app.glossary.models import GlossaryRecord
from app.glossary.query import GlossaryQuery
from app.linguistic.word_count import count_words
from app.models import DocumentStatus, MachineTranslationSettings, TaskStatus
from app.schema import DocumentTask
from app.translation_memory.models import TranslationMemoryRecord
from app.translation_memory.query import TranslationMemoryQuery
from app.translators import llm, yandex
from app.translators.common import LineWithGlossaries

type FormatSegment = XliffSegment | TxtSegment


class RecordSource(Enum):
    glossary = "glossary"
    machine_translation = "mt"
    translation_memory = "tm"
    full_match = "fm"  # for digits


class WorkerSegment:
    @overload
    def __init__(
        self, *, type_: Literal["xliff"], original_segment: XliffSegment
    ) -> None: ...

    @overload
    def __init__(
        self, *, type_: Literal["txt"], original_segment: TxtSegment
    ) -> None: ...

    def __init__(
        self,
        *,
        type_: Literal["xliff", "txt"],
        original_segment: FormatSegment,
    ) -> None:
        self._segment_src = None
        self._type = type_
        self._approved = False
        self.original_segment = original_segment
        assert (type_ == "xliff" and isinstance(original_segment, XliffSegment)) or (
            type_ == "txt" and isinstance(original_segment, TxtSegment)
        )
        if isinstance(original_segment, XliffSegment):
            self._approved = original_segment.approved

    @property
    def segment_source(self) -> RecordSource | None:
        return self._segment_src

    @segment_source.setter
    def segment_source(self, value: RecordSource | None):
        self._segment_src = value

    @property
    def approved(self):
        return self._approved

    @approved.setter
    def approved(self, value: bool):
        self._approved = value

    @property
    def type_(self):
        return self._type

    @property
    def needs_processing(self) -> bool:
        if isinstance(self.original_segment, XliffSegment):
            return not self.original_segment.approved
        return True


def get_segment_translation(
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


def process_document(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
) -> bool:
    tm_ids = [x.id for x in doc.memories]
    glossary_ids = [x.id for x in doc.glossaries]

    start_time = time.time()
    segments = extract_segments(doc)
    logging.info(
        "Segments extraction time: %.2f seconds, speed: %.2f segment/second",
        time.time() - start_time,
        len(segments) / (time.time() - start_time + 0.01),
    )

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


def extract_segments(doc: Document) -> Sequence[WorkerSegment]:
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

        translation = get_segment_translation(
            segment.original_segment.original,
            settings.similarity_threshold,
            tm_ids,
            glossary_ids,
            session,
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
