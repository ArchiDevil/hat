import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.db import get_db
from app.documents.models import Document, DocumentType, XliffDocument, XliffRecord
from app.documents.schema import (
    DocumentTaskDescription,
    DocumentProcessingSettings,
    TmxUsage,
)
from app.models import DocumentStatus, MachineTranslationSettings
from app.schema import DocumentTask, TmxDocument, TmxRecord
from worker import process_task

# pylint: disable=C0116


def get_session() -> Session:
    return next(get_db())


def test_process_task_sets_records(session: Session):
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
                Document(
                    name="small.xliff",
                    type=DocumentType.XLIFF,
                    created_by=1,
                    processing_status=DocumentStatus.PENDING.value,
                    upload_time=datetime.now(),
                ),
                XliffDocument(
                    parent_id=1,
                    original_document=file_data,
                ),
            ]
        )

        task = DocumentTask(
            data=DocumentTaskDescription(
                type="xliff",
                document_id=1,
                settings=DocumentProcessingSettings(
                    substitute_numbers=False,
                    machine_translation_settings=None,
                    tmx_file_ids=[1],
                    tmx_usage=TmxUsage.NEWEST,
                ),
            ).model_dump_json(),
            status="pending",
        )
        s.add(task)
        s.commit()

        result = process_task(s, task)
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4

        # It provides text for matching TMX record
        record = doc.records[0]
        assert record.id == 1
        assert record.document_id == 1
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
        assert record.id == 2
        assert record.document_id == 1
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
        assert record.id == 3
        assert record.document_id == 1
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
        assert record.id == 4
        assert record.document_id == 1
        assert record.source == "123456789"
        assert record.target == ""
        xliff_record = (
            s.query(XliffRecord).filter(XliffRecord.parent_id == record.id).one()
        )
        assert xliff_record.segment_id == 675609
        assert xliff_record.state == "needs-translation"
        assert not xliff_record.approved


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
                Document(
                    name="small.xliff",
                    type=DocumentType.XLIFF,
                    created_by=1,
                    processing_status=DocumentStatus.PENDING.value,
                    upload_time=datetime.now(),
                ),
                XliffDocument(
                    parent_id=1,
                    original_document=file_data,
                ),
                DocumentTask(
                    data=DocumentTaskDescription(
                        type="xliff",
                        document_id=1,
                        settings=DocumentProcessingSettings(
                            substitute_numbers=False,
                            machine_translation_settings=None,
                            tmx_file_ids=[2],
                            tmx_usage=TmxUsage.NEWEST,
                        ),
                    ).model_dump_json(),
                    status="pending",
                ),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It provides text for matching TMX record
        assert doc.records[0].id == 1
        assert doc.records[0].document_id == 1
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Another translation"
        xliff_record = (
            s.query(XliffRecord)
            .filter(XliffRecord.parent_id == doc.records[0].id)
            .one()
        )
        assert xliff_record.segment_id == 675606


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
                Document(
                    name="small.xliff",
                    type=DocumentType.XLIFF,
                    created_by=1,
                    processing_status=DocumentStatus.PENDING.value,
                    upload_time=datetime.now(),
                ),
                XliffDocument(
                    parent_id=1,
                    original_document=file_data,
                ),
                DocumentTask(
                    data=DocumentTaskDescription(
                        type="xliff",
                        document_id=1,
                        settings=DocumentProcessingSettings(
                            substitute_numbers=False,
                            machine_translation_settings=None,
                            tmx_file_ids=[1, 2],
                            tmx_usage=TmxUsage(mode),
                        ),
                    ).model_dump_json(),
                    status="pending",
                ),
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
                Document(
                    name="small.xliff",
                    type=DocumentType.XLIFF,
                    created_by=1,
                    processing_status=DocumentStatus.PENDING.value,
                    upload_time=datetime.now(),
                ),
                XliffDocument(
                    parent_id=1,
                    original_document=file_data,
                ),
                DocumentTask(
                    data=DocumentTaskDescription(
                        type="xliff",
                        document_id=1,
                        settings=DocumentProcessingSettings(
                            substitute_numbers=True,
                            machine_translation_settings=None,
                            tmx_file_ids=[1],
                            tmx_usage=TmxUsage.NEWEST,
                        ),
                    ).model_dump_json(),
                    status="pending",
                ),
            ]
        )
        s.commit()

        result = process_task(s, s.query(DocumentTask).one())
        assert result

        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It substitutes numbers
        assert doc.records[3].id == 4
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == "123456789"
        xliff_record = (
            s.query(XliffRecord)
            .filter(XliffRecord.parent_id == doc.records[3].id)
            .one()
        )
        assert xliff_record.segment_id == 675609


def test_process_task_checks_task_data_attributes(session: Session):
    with session as s:
        datas = [
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
        ]

        for data in datas:
            s.add(DocumentTask(data=json.dumps(data), status="pending"))
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
                Document(
                    name="small.xliff",
                    type=DocumentType.XLIFF,
                    created_by=1,
                    processing_status=DocumentStatus.PENDING.value,
                    upload_time=datetime.now(),
                ),
                XliffDocument(
                    parent_id=1,
                    original_document=file_data,
                ),
                DocumentTask(
                    data=DocumentTaskDescription(
                        type="xliff",
                        document_id=1,
                        settings=DocumentProcessingSettings(
                            substitute_numbers=False,
                            machine_translation_settings=MachineTranslationSettings(
                                folder_id="12345", oauth_token="fake"
                            ),
                            tmx_file_ids=[],
                            tmx_usage=TmxUsage.NEWEST,
                        ),
                    ).model_dump_json(),
                    status="pending",
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
