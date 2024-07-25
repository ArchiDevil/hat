# This is a worker that takes tasks from the database every 10 seconds and
# processes XLIFF files in it.
# Tasks are stored in document_task table and encoded in JSON.

import json
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db, models
from app.documents.models import Document, DocumentRecord
from app.documents.query import GenericDocsQuery
from app.documents.schema import DocumentProcessingSettings
from app.schema import DocumentTask, TmxRecord, XliffRecord
from app.translation_memory.utils import get_substitutions
from app.translators import yandex
from app.xliff import extract_xliff_content


def get_segment_translation(
    source: str,
    settings: DocumentProcessingSettings,
    session: Session,
):
    # TODO: this would be nice to have batching for all segments to reduce amounts of requests to DB
    if settings.substitute_numbers and source.isdigit():
        return source

    if settings.similarity_threshold < 1.0:
        substitutions = get_substitutions(
            source, settings.tmx_file_ids, session, settings.similarity_threshold, 1
        )
        if substitutions:
            return substitutions[0].target
    else:
        selector = (
            select(TmxRecord.source, TmxRecord.target)
            .where(TmxRecord.source == source)
            .where(TmxRecord.document_id.in_(settings.tmx_file_ids))
        )
        match settings.tmx_usage:
            case models.TmxUsage.NEWEST:
                selector = selector.order_by(TmxRecord.change_date.desc())
            case models.TmxUsage.OLDEST:
                selector = selector.order_by(TmxRecord.change_date.asc())
            case _:
                logging.error("Unknown TMX usage option")
                return None

        tmx_data = session.execute(selector.limit(1)).first()

        if tmx_data:
            return tmx_data.target

    return None


def process_xliff(
    doc: Document,
    settings: DocumentProcessingSettings,
    session: Session,
):
    xliff_document = doc.xliff
    xliff_data = extract_xliff_content(xliff_document.original_document.encode())
    to_translate: list[int] = []
    for i, segment in enumerate(xliff_data.segments):
        if not segment.approved:
            translation = get_segment_translation(segment.original, settings, session)
            if not translation:
                # we cannot find translation for this segment
                # save it to translate by Yandex
                to_translate.append(i)
                continue

            segment.translation = translation if translation else ""

    # translate by Yandex if there is a setting to do so enabled
    # TODO: it is better to make solution more translation service agnostic
    machine_translation_failed = False
    if settings.machine_translation_settings and len(to_translate) > 0:
        if (
            not settings.machine_translation_settings
            or not settings.machine_translation_settings.folder_id
            or not settings.machine_translation_settings.oauth_token
        ):
            # TODO: this should never happen, how to check it with Pydantic?
            logging.error(
                "Machine translation settings are not configured, %s", settings
            )
            return False

        try:
            lines = [xliff_data.segments[i].original for i in to_translate]
            translated, failed = yandex.translate_lines(
                lines,
                settings.machine_translation_settings,
            )
            machine_translation_failed = failed
            for i, translated_line in enumerate(translated):
                xliff_data.segments[to_translate[i]].translation = translated_line
        # TODO: handle specific exceptions instead of a generic one
        except Exception as e:
            logging.error("Yandex translation error %s", e)
            return False

    doc_records = []
    for segment in xliff_data.segments:
        doc_records.append(
            DocumentRecord(
                document_id=doc.id,
                source=segment.original,
                target=segment.translation,
            )
        )
    session.add_all(doc_records)
    session.commit()

    for i, segment in enumerate(xliff_data.segments):
        xliff_record = XliffRecord(
            parent_id=doc_records[i].id,
            document_id=xliff_document.id,
            segment_id=segment.id_,
            state=segment.state.value,
            approved=segment.approved,
        )
        session.add(xliff_record)
    session.commit()

    return not machine_translation_failed


def process_task(session: Session, task: DocumentTask) -> bool:
    try:
        task.status = models.TaskStatus.PROCESSING.value
        session.commit()

        logging.info("New task found: %s", task.id)

        task_data: dict = json.loads(task.data)
        if "type" not in task_data:
            logging.error("Task data is missing 'type' field")
            raise AttributeError("Task data 'type' field")

        if task_data["type"] != "xliff":
            logging.error("Task data 'type' field is not 'xliff'")
            raise AttributeError("Task data 'type' field is not 'xliff'")

        if "doc_id" not in task_data:
            logging.error("Task data is missing 'doc_id' field")
            raise AttributeError("Task data 'doc_id' field")

        if "settings" not in task_data or not task_data["settings"]:
            logging.error("Task data is missing 'settings' field")
            raise AttributeError("Task data is missing 'settings' field")

        document_id = task_data["doc_id"]
        doc = GenericDocsQuery(session).get_document(document_id)

        # TODO: what if the doc processing was started and left in a processing state?
        if not doc or doc.processing_status != models.DocumentStatus.PENDING.value:
            logging.error("Document not found or not in a pending state")
            return False

        settings = DocumentProcessingSettings.model_validate_json(task_data["settings"])

        doc.processing_status = models.DocumentStatus.PROCESSING.value
        session.commit()

        if not process_xliff(doc, settings, session):
            doc.processing_status = models.DocumentStatus.ERROR.value
            session.commit()
            logging.error("Processing failed for document %d", doc.id)
            return False

        doc.processing_status = models.DocumentStatus.DONE.value
        session.commit()
        return True
    except Exception as e:
        logging.error("Task processing failed: %s", str(e))
        return False
    finally:
        logging.info("Task finished %s, removing...", task.id)
        session.delete(task)
        session.commit()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Starting document processing")

    session = next(db.get_db())
    while True:
        task = session.query(DocumentTask).first()
        if not task:
            time.sleep(10)
            continue

        process_task(session, task)


if __name__ == "__main__":
    main()
