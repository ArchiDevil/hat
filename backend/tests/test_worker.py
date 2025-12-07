import json
from datetime import datetime
from typing import Literal

import pytest
from sqlalchemy.orm import Session

from app.db import get_db
from app.documents.models import (
    DocGlossaryAssociation,
    DocMemoryAssociation,
    Document,
    DocumentType,
    TxtDocument,
    TxtRecord,
    XliffDocument,
    XliffRecord,
)
from app.documents.schema import (
    DocumentProcessingSettings,
    DocumentTaskDescription,
)
from app.glossary.models import Glossary, GlossaryRecord
from app.models import (
    DocumentStatus,
    YandexTranslatorSettings,
)
from app.schema import DocumentTask
from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord
from worker import process_task

# pylint: disable=C0116


def get_session() -> Session:
    return next(get_db())


def create_doc(name: str, type_: DocumentType):
    return Document(
        name=name,
        type=type_,
        created_by=1,
        processing_status=DocumentStatus.PENDING.value,
        upload_time=datetime.now(),
    )


def create_xliff_doc(data: str):
    return XliffDocument(parent_id=1, original_document=data)


def create_task(
    *,
    type_: Literal["xliff", "txt"] = "xliff",
    mt_settings: YandexTranslatorSettings | None = None,
):
    return DocumentTask(
        data=DocumentTaskDescription(
            type=type_,
            document_id=1,
            settings=DocumentProcessingSettings(
                machine_translation_settings=mt_settings,
            ),
        ).model_dump_json(),
        status="pending",
    )


def test_process_task_sets_xliff_records(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        s.add_all(
            [
                TranslationMemory(
                    name="test",
                    records=[
                        TranslationMemoryRecord(
                            source="Regional Effects",
                            target="Translation",
                        )
                    ],
                    created_by=1,
                ),
                create_doc(name="small.xliff", type_=DocumentType.xliff),
                create_xliff_doc(file_data),
                DocMemoryAssociation(doc_id=1, tm_id=1, mode="read"),
            ]
        )

        task = create_task()
        s.add(task)
        s.commit()

        result = process_task(s, task)
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4

        assert all(record.document_id == 1 for record in doc.records)
        assert all(record.id == idx + 1 for idx, record in enumerate(doc.records))

        # It provides text for matching TM record
        record = doc.records[0]
        assert record.source == "Regional Effects"
        assert record.target == "Translation"
        assert not record.approved
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675606
        assert xliff_record.state == "translated"

        # It does not provide text for missing TM record
        record = doc.records[1]
        assert record.source == "Other Effects"
        assert record.target == ""
        assert not record.approved
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675607
        assert xliff_record.state == "needs-translation"

        # It does not touch approved record
        record = doc.records[2]
        assert record.source == "Regional Effects"
        assert record.target == "Региональные эффекты"
        assert record.approved
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675608
        assert xliff_record.state == "translated"

        # It does substitute numbers
        record = doc.records[3]
        assert record.source == "123456789"
        assert record.target == "123456789"
        assert not record.approved
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675609
        assert xliff_record.state == "translated"


def test_process_task_sets_txt_records(session: Session):
    with open("tests/fixtures/small.txt", "r", encoding="utf-8", newline="") as fp:
        file_data = fp.read()

    crlf = "\r\n" in file_data

    with session as s:
        s.add_all(
            [
                TranslationMemory(
                    name="test",
                    records=[
                        TranslationMemoryRecord(
                            source="The sloth is named Razak.", target="Translation"
                        )
                    ],
                    created_by=1,
                ),
                create_doc(name="small.txt", type_=DocumentType.txt),
                TxtDocument(parent_id=1, original_document=file_data),
                DocMemoryAssociation(doc_id=1, tm_id=1, mode="read"),
            ]
        )

        task = create_task(type_="txt")
        s.add(task)
        s.commit()

        result = process_task(s, task)
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 6

        assert all(record.document_id == 1 for record in doc.records)
        assert all(record.id == idx + 1 for idx, record in enumerate(doc.records))

        record = doc.records[0]
        assert (
            record.source
            == "Soon after the characters enter Camp Greenbriar, read or paraphrase the following text:"
        )
        assert not record.target
        assert s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 0

        record = doc.records[1]
        assert (
            record.source
            == "“Hello, travelers!” calls an energetic giant sloth wearing a bracelet of claws and feathers."
        )
        assert not record.target
        assert (
            s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 91
            if crlf
            else 89
        )

        record = doc.records[2]
        assert (
            record.source
            == "The creature dangles from a nearby tree and waves a three-clawed paw."
        )
        assert not record.target
        assert (
            s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 184
            if crlf
            else 182
        )

        record = doc.records[3]
        assert record.source == "“Fresh faces are always welcome in Camp Greenbriar!”"
        assert not record.target
        assert (
            s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 254
            if crlf
            else 252
        )

        record = doc.records[4]
        assert record.source == "The sloth is named Razak."
        assert record.target == "Translation"
        assert (
            s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 310
            if crlf
            else 306
        )

        record = doc.records[5]
        assert (
            record.source
            == "He uses black bear stat block, with the following adjustments:"
        )
        assert not record.target
        assert (
            s.query(TxtRecord).filter_by(parent_id=record.id).one().offset == 336
            if crlf
            else 332
        )


def test_process_task_uses_correct_tm_ids(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tm_records_1 = [
            TranslationMemoryRecord(source="Regional Effects", target="Translation"),
            TranslationMemoryRecord(source="Test", target="Segment"),
        ]
        tm_records_2 = [
            TranslationMemoryRecord(
                source="Regional Effects", target="Another translation"
            )
        ]
        s.add_all(
            [
                TranslationMemory(name="test1", records=tm_records_1, created_by=1),
                TranslationMemory(name="test2", records=tm_records_2, created_by=1),
                create_doc(name="small.xliff", type_=DocumentType.xliff),
                create_xliff_doc(file_data),
                create_task(),
                DocMemoryAssociation(doc_id=1, tm_id=2, mode="read"),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Another translation"


@pytest.mark.parametrize(
    "task_data",
    [
        {
            "document_id": 1,
            "settings": {
                "use_machine_translation": False,
                "machine_translation_settings": None,
            },
        },
        {
            "type": "xliff",
            "settings": {
                "use_machine_translation": False,
                "machine_translation_settings": None,
            },
        },
        {
            "type": "xliff",
            "document_id": 1,
        },
        {
            "type": "broken",
            "document_id": 1,
            "settings": {
                "use_machine_translation": False,
                "machine_translation_settings": None,
            },
        },
    ],
)
def test_process_task_checks_task_data_attributes(session: Session, task_data: str):
    with session as s:
        s.add(DocumentTask(data=json.dumps(task_data), status="pending"))
        s.commit()

        tasks = s.query(DocumentTask).all()
        for task in tasks:
            assert not process_task(session, task)


def test_process_task_deletes_task_after_processing(session: Session):
    with session as s:
        task = DocumentTask(data=json.dumps({"doc_id": 1}), status="pending")
        s.add(task)
        s.commit()

        process_task(s, task)
        assert not s.query(DocumentTask).first()


def test_process_task_puts_doc_in_error_state(monkeypatch, session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        s.add_all(
            [
                create_doc(name="small.xliff", type_=DocumentType.xliff),
                create_xliff_doc(file_data),
                create_task(
                    mt_settings=YandexTranslatorSettings(
                        type="yandex", folder_id="12345", oauth_token="fake"
                    ),
                ),
            ]
        )
        s.commit()

        def fake_translate(*args, **kwargs):
            raise RuntimeError()

        monkeypatch.setattr("app.translators.yandex.translate_lines", fake_translate)

        try:
            process_task(s, s.query(DocumentTask).one())
        except AttributeError:
            pass

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "error"


def test_process_task_uses_correct_glossary_ids(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        glossary_records_1 = [
            GlossaryRecord(
                source="Regional Effects",
                target="Glossary entry 1",
                created_by=1,
                stemmed_source="regional effects",
            )
        ]
        glossary_records_2 = [
            GlossaryRecord(
                source="Regional Effects",
                target="Glossary entry 2",
                created_by=1,
                stemmed_source="regional effects",
            )
        ]

        s.add_all(
            [
                Glossary(name="test1", created_by=1, records=glossary_records_1),
                Glossary(name="test2", created_by=1, records=glossary_records_2),
                create_doc(name="small.xliff", type_=DocumentType.xliff),
                create_xliff_doc(file_data),
                create_task(),
                DocGlossaryAssociation(document_id=1, glossary_id=2),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()

        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Glossary entry 2"
