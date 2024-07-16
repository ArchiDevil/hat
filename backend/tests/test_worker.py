import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app import models, schema
from app.db import get_db
from worker import process_task

# pylint: disable=C0116


def get_session() -> Session:
    return next(get_db())


def test_process_task_sets_records(session: Session):
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records = [
            schema.TmxRecord(
                source="Regional Effects",
                target="Translation",
            )
        ]
        s.add(schema.TmxDocument(name="test", records=tmx_records, created_by=1))
        s.commit()

        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {
                    "substitute_numbers": False,
                    "use_machine_translation": False,
                    "machine_translation_settings": None,
                    "tmx_file_ids": [1],
                    "tmx_usage": "newest",
                }
            ),
        }
        s.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        s.commit()

        result = process_task(s, s.query(schema.DocumentTask).one())
        assert result

        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It provides text for matching TMX record
        assert doc.records[0].id == 1
        assert doc.records[0].segment_id == 675606
        assert doc.records[0].document_id == 1
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Translation"
        assert doc.records[0].state == "translated"
        assert not doc.records[0].approved
        # It does not provide text for missing TMX record
        assert doc.records[1].id == 2
        assert doc.records[1].segment_id == 675607
        assert doc.records[1].document_id == 1
        assert doc.records[1].source == "Other Effects"
        assert doc.records[1].target == ""
        assert doc.records[1].state == "needs-translation"
        assert not doc.records[1].approved
        # It does not touch approved record
        assert doc.records[2].id == 3
        assert doc.records[2].segment_id == 675608
        assert doc.records[2].document_id == 1
        assert doc.records[2].source == "Regional Effects"
        assert doc.records[2].target == "Региональные эффекты"
        assert doc.records[2].state == "translated"
        assert doc.records[2].approved
        # It does not substitute numbers
        assert doc.records[3].id == 4
        assert doc.records[3].segment_id == 675609
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == ""
        assert doc.records[3].state == "needs-translation"
        assert not doc.records[3].approved


def test_process_task_uses_correct_tmx_ids(session: Session):
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records_1 = [
            schema.TmxRecord(source="Regional Effects", target="Translation"),
            schema.TmxRecord(source="Test", target="Segment"),
        ]
        tmx_records_2 = [
            schema.TmxRecord(source="Regional Effects", target="Another translation")
        ]
        s.add(schema.TmxDocument(name="test1", records=tmx_records_1, created_by=1))
        s.add(schema.TmxDocument(name="test2", records=tmx_records_2, created_by=1))
        s.commit()

        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {
                    "substitute_numbers": False,
                    "use_machine_translation": False,
                    "machine_translation_settings": None,
                    "tmx_file_ids": [2],
                    "tmx_usage": "newest",
                }
            ),
        }
        s.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        s.commit()

        result = process_task(s, s.query(schema.DocumentTask).one())
        assert result

        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It provides text for matching TMX record
        assert doc.records[0].id == 1
        assert doc.records[0].segment_id == 675606
        assert doc.records[0].document_id == 1
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Another translation"


@pytest.mark.parametrize(
    ["mode", "trans_result"],
    [("newest", "Another translation"), ("oldest", "Translation")],
)
def test_process_task_uses_tmx_mode(mode: str, trans_result: str, session: Session):
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records_1 = [
            schema.TmxRecord(
                source="Regional Effects",
                target="Translation",
                creation_date=datetime(2020, 1, 1, 0, 0, 0),
                change_date=datetime(2020, 1, 1, 0, 0, 0),
            )
        ]
        tmx_records_2 = [
            schema.TmxRecord(
                source="Regional Effects",
                target="Another translation",
                creation_date=datetime(2021, 1, 1, 0, 0, 0),
                change_date=datetime(2021, 1, 1, 0, 0, 0),
            )
        ]
        s.add(schema.TmxDocument(name="test1", records=tmx_records_1, created_by=1))
        s.add(schema.TmxDocument(name="test2", records=tmx_records_2, created_by=1))
        s.commit()

        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {
                    "substitute_numbers": False,
                    "use_machine_translation": False,
                    "machine_translation_settings": None,
                    "tmx_file_ids": [1, 2],
                    "tmx_usage": mode,
                }
            ),
        }
        s.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        s.commit()

        result = process_task(s, s.query(schema.DocumentTask).one())
        assert result

        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) > 1
        assert doc.records[0].target == trans_result


def test_process_task_substitutes_numbers(session: Session):
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        tmx_records = []
        s.add(schema.TmxDocument(name="test", records=tmx_records, created_by=1))
        s.commit()

        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {
                    "substitute_numbers": True,
                    "use_machine_translation": False,
                    "machine_translation_settings": None,
                    "tmx_file_ids": [1],
                    "tmx_usage": "newest",
                }
            ),
        }
        s.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        s.commit()

        result = process_task(s, s.query(schema.DocumentTask).one())
        assert result

        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It substitutes numbers
        assert doc.records[3].id == 4
        assert doc.records[3].segment_id == 675609
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == "123456789"


def test_process_task_checks_task_data_attributes(session: Session):
    with session as s:
        datas = [
            {
                "doc_id": 1,
                "settings": json.dumps(
                    {
                        "substitute_numbers": False,
                        "use_machine_translation": False,
                        "machine_translation_settings": None,
                        "tmx_file_ids": [1],
                        "tmx_usage": "newest",
                    }
                ),
            },
            {
                "type": "xliff",
                "settings": json.dumps(
                    {
                        "substitute_numbers": False,
                        "use_machine_translation": False,
                        "machine_translation_settings": None,
                        "tmx_file_ids": [1],
                        "tmx_usage": "newest",
                    }
                ),
            },
            {
                "type": "xliff",
                "doc_id": 1,
            },
            {
                "type": "broken",
                "doc_id": 1,
                "settings": json.dumps(
                    {
                        "substitute_numbers": False,
                        "use_machine_translation": False,
                        "machine_translation_settings": None,
                        "tmx_file_ids": [1],
                        "tmx_usage": "newest",
                    }
                ),
            },
        ]

        for data in datas:
            s.add(schema.DocumentTask(data=json.dumps(data), status="pending"))
        s.commit()

        tasks = s.query(schema.DocumentTask).all()
        for task in tasks:
            assert not process_task(session, task)


def test_process_task_deletes_task_after_processing(session: Session):
    with session as s:
        task = schema.DocumentTask(data=json.dumps({"doc_id": 1}), status="pending")
        s.add(task)
        s.commit()

        process_task(s, task)
        assert not s.query(schema.DocumentTask).first()


def test_process_task_puts_doc_in_error_state(monkeypatch, session: Session):
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with session as s:
        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {
                    "substitute_numbers": False,
                    "use_machine_translation": True,
                    "machine_translation_settings": {
                        "folder_id": "12345",
                        "oauth_token": "fake",
                    },
                    "tmx_file_ids": [],
                    "tmx_usage": "newest",
                }
            ),
        }
        s.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        s.commit()

        def fake_translate(*args, **kwargs):
            raise RuntimeError()

        monkeypatch.setattr("app.translators.yandex.translate_lines", fake_translate)

        try:
            process_task(s, s.query(schema.DocumentTask).one())
        except AttributeError:
            pass

        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "error"
