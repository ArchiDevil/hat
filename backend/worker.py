# This is a worker that takes tasks from the database every 10 seconds and
# processes XLIFF files in it.
# Tasks are stored in document_task table and encoded in JSON.

import json
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db, models, schema
from app.xliff import extract_xliff_content, XliffSegment
from app.translators import yandex


def get_segment_translation(
    segment: XliffSegment,
    settings: models.XliffProcessingSettings,
    session: Session,
):
    # TODO: this is slow, it needs to be optimized
    tmx_data = session.execute(
        select(schema.TmxRecord.source, schema.TmxRecord.target)
        .where(schema.TmxRecord.source == segment.original)
        .limit(1)
    ).first()

    if tmx_data:
        return tmx_data.target

    if settings.substitute_numbers and segment.original.isdigit():
        return segment.original

    return None


def process_xliff(
    doc: schema.XliffDocument,
    settings: models.XliffProcessingSettings,
    session: Session,
):
    xliff_data = extract_xliff_content(doc.original_document.encode())
    to_translate: list[int] = []
    for i, segment in enumerate(xliff_data.segments):
        if not segment.approved:
            translation = get_segment_translation(segment, settings, session)
            if not translation:
                # we cannot find translation for this segment
                # save it to translate by Yandex
                to_translate.append(i)

            segment.translation = translation if translation else ""

    # translate by Yandex if there is a setting to do so enabled
    # TODO: it is better to make solution more translation service agnostic
    if settings.use_machine_translation and len(to_translate) > 0:
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
            translated = yandex.translate_lines(
                lines,
                settings.machine_translation_settings,
            )
            for i, translated_line in enumerate(translated):
                xliff_data.segments[to_translate[i]].translation = translated_line
        # TODO: handle specific exceptions instead of a generic one
        except Exception as e:
            logging.error("Yandex translation error %s", e)
            return False

    for segment in xliff_data.segments:
        doc.records.append(
            schema.XliffRecord(
                segment_id=segment.id_,
                source=segment.original,
                target=segment.translation,
            )
        )

    return True


def process_task(session: Session, task: schema.DocumentTask) -> bool:
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
        doc = (
            session.query(schema.XliffDocument)
            .filter(schema.XliffDocument.id == document_id)
            .first()
        )

        # TODO: what if the doc processing was started and left in a processing state?
        if not doc or doc.processing_status != models.DocumentStatus.PENDING.value:
            logging.error("Document not found or not in a pending state")
            return False

        settings = models.XliffProcessingSettings.model_validate_json(
            task_data["settings"]
        )

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
        task = session.query(schema.DocumentTask).first()
        if not task:
            time.sleep(10)
            continue

        process_task(session, task)


if __name__ == "__main__":
    main()
