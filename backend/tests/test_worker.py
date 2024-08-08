import json
from datetime import datetime
from typing import Literal

import pytest
from sqlalchemy.orm import Session

from app.db import get_db
from app.documents.models import (
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
    TmxUsage,
)
from app.models import DocumentStatus, MachineTranslationSettings
from app.schema import DocumentTask, TmxDocument, TmxRecord
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
    tmx_ids=[1],
    usage: TmxUsage = TmxUsage.NEWEST,
    substitute_numbers: bool = False,
    mt_settings: MachineTranslationSettings | None = None,
):
    return DocumentTask(
        data=DocumentTaskDescription(
            type=type_,
            document_id=1,
            settings=DocumentProcessingSettings(
                substitute_numbers=substitute_numbers,
                machine_translation_settings=mt_settings,
                tmx_file_ids=tmx_ids,
                tmx_usage=usage,
            ),
        ).model_dump_json(),
        status="pending",
    )


def test_process_task_sets_xliff_records(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records = [
            TmxRecord(
                source="Regional Effects",
                target="Translation",
            )
        ]
        s.add_all(
            [
                TmxDocument(name="test", records=tmx_records, created_by=1),
                create_doc(name="small.xliff", type_=DocumentType.XLIFF),
                create_xliff_doc(file_data),
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

        # It provides text for matching TMX record
        record = doc.records[0]
        assert record.source == "Regional Effects"
        assert record.target == "Translation"
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675606
        assert xliff_record.state == "translated"
        assert not xliff_record.approved

        # It does not provide text for missing TMX record
        record = doc.records[1]
        assert record.source == "Other Effects"
        assert record.target == ""
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675607
        assert xliff_record.state == "needs-translation"
        assert not xliff_record.approved

        # It does not touch approved record
        record = doc.records[2]
        assert record.source == "Regional Effects"
        assert record.target == "Региональные эффекты"
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675608
        assert xliff_record.state == "translated"
        assert xliff_record.approved

        # It does not substitute numbers
        record = doc.records[3]
        assert record.source == "123456789"
        assert record.target == ""
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675609
        assert xliff_record.state == "needs-translation"
        assert not xliff_record.approved


def test_process_task_sets_txt_records(session: Session):
    with open("tests/fixtures/small.txt", "r", encoding="utf-8", newline="") as fp:
        file_data = fp.read()

    crlf = "\r\n" in file_data

    with session as s:
        s.add_all(
            [
                TmxDocument(
                    name="test",
                    records=[
                        TmxRecord(
                            source="The sloth is named Razak.", target="Translation"
                        )
                    ],
                    created_by=1,
                ),
                create_doc(name="small.txt", type_=DocumentType.TXT),
                TxtDocument(parent_id=1, original_document=file_data),
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


def test_process_task_uses_correct_tmx_ids(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records_1 = [
            TmxRecord(source="Regional Effects", target="Translation"),
            TmxRecord(source="Test", target="Segment"),
        ]
        tmx_records_2 = [
            TmxRecord(source="Regional Effects", target="Another translation")
        ]
        s.add_all(
            [
                TmxDocument(name="test1", records=tmx_records_1, created_by=1),
                TmxDocument(name="test2", records=tmx_records_2, created_by=1),
                create_doc(name="small.xliff", type_=DocumentType.XLIFF),
                create_xliff_doc(file_data),
                create_task(tmx_ids=[2]),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Another translation"


@pytest.mark.parametrize(
    ["mode", "trans_result"],
    [("newest", "Another translation"), ("oldest", "Translation")],
)
def test_process_task_uses_tmx_mode(mode: str, trans_result: str, session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records_1 = [
            TmxRecord(
                source="Regional Effects",
                target="Translation",
                creation_date=datetime(2020, 1, 1, 0, 0, 0),
                change_date=datetime(2020, 1, 1, 0, 0, 0),
            )
        ]
        tmx_records_2 = [
            TmxRecord(
                source="Regional Effects",
                target="Another translation",
                creation_date=datetime(2021, 1, 1, 0, 0, 0),
                change_date=datetime(2021, 1, 1, 0, 0, 0),
            )
        ]
        s.add_all(
            [
                TmxDocument(name="test1", records=tmx_records_1, created_by=1),
                TmxDocument(name="test2", records=tmx_records_2, created_by=1),
                create_doc(name="small.xliff", type_=DocumentType.XLIFF),
                create_xliff_doc(file_data),
                create_task(tmx_ids=[1, 2], usage=TmxUsage(mode)),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) > 1
        assert doc.records[0].target == trans_result


def test_process_task_substitutes_numbers(session: Session):
    with open("tests/fixtures/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        s.add_all(
            [
                TmxDocument(name="test", records=[], created_by=1),
                create_doc(name="small.xliff", type_=DocumentType.XLIFF),
                create_xliff_doc(file_data),
                create_task(substitute_numbers=True),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == "123456789"


@pytest.mark.parametrize(
    "task_data",
    [
        {
            "document_id": 1,
            "settings": {
                "substitute_numbers": False,
                "use_machine_translation": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
            },
        },
        {
            "type": "xliff",
            "settings": {
                "substitute_numbers": False,
                "use_machine_translation": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
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
                "substitute_numbers": False,
                "use_machine_translation": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
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
                create_doc(name="small.xliff", type_=DocumentType.XLIFF),
                create_xliff_doc(file_data),
                create_task(
                    tmx_ids=[],
                    mt_settings=MachineTranslationSettings(
                        folder_id="12345", oauth_token="fake"
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
