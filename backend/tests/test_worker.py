from datetime import datetime, timedelta
import json
import os
import tempfile

import pytest
from sqlalchemy.orm import Session

from app import db, models, schema
from app.db import get_db, init_connection

from worker import process_task


@pytest.fixture(autouse=True, scope="function")
def connection():
    db_fd, db_path = tempfile.mkstemp()
    init_connection(f"sqlite:///{db_path}")
    assert db.engine and db.SessionLocal

    schema.Base.metadata.drop_all(db.engine)
    schema.Base.metadata.create_all(db.engine)

    yield

    db.close_connection()
    os.close(db_fd)
    os.unlink(db_path)


def get_session() -> Session:
    return next(get_db())


def test_worker_sets_records():
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with get_session() as session:
        tmx_records = [
            schema.TmxRecord(source="Regional Effects", target="Translation")
        ]
        session.add(schema.TmxDocument(name="test", records=tmx_records))
        session.commit()

        session.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {"substitute_numbers": False, "use_machine_translation": False}
            ),
        }
        session.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        session.commit()

        result = process_task(session, session.query(schema.DocumentTask).one())
        assert result

        doc = session.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It provides text for matching TMX record
        assert doc.records[0].id == 1
        assert doc.records[0].segment_id == 675606
        assert doc.records[0].document_id == 1
        assert doc.records[0].source == "Regional Effects"
        assert doc.records[0].target == "Translation"
        # It does not provide text for missing TMX record
        assert doc.records[1].id == 2
        assert doc.records[1].segment_id == 675607
        assert doc.records[1].document_id == 1
        assert doc.records[1].source == "Other Effects"
        assert doc.records[1].target == ""
        # It does not touch approved record
        assert doc.records[2].id == 3
        assert doc.records[2].segment_id == 675608
        assert doc.records[2].document_id == 1
        assert doc.records[2].source == "Regional Effects"
        assert doc.records[2].target == "Региональные эффекты"
        # It does not substitute numbers
        assert doc.records[3].id == 4
        assert doc.records[3].segment_id == 675609
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == ""


def test_worker_substitutes_numbers():
    with open("tests/small.xliff", "r", encoding="utf-8") as fp:
        file_data = fp.read()

    with get_session() as session:
        tmx_records = []
        session.add(schema.TmxDocument(name="test", records=tmx_records))
        session.commit()

        session.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document=file_data,
                processing_status=models.DocumentStatus.PENDING.value,
                upload_time=(datetime.now() - timedelta(days=2)),
            )
        )

        task_data = {
            "type": "xliff",
            "doc_id": 1,
            "settings": json.dumps(
                {"substitute_numbers": True, "use_machine_translation": False}
            ),
        }
        session.add(
            schema.DocumentTask(
                data=json.dumps(task_data),
                status="pending",
            )
        )
        session.commit()

        result = process_task(session, session.query(schema.DocumentTask).one())
        assert result

        doc = session.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It substitutes numbers
        assert doc.records[3].id == 4
        assert doc.records[3].segment_id == 675609
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == "123456789"
