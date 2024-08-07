import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, schema
from app.documents.models import Document, DocumentRecord

# pylint: disable=C0116


def test_can_get_list_of_docs(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add_all(
            [
                Document(
                    name="first_doc.xliff",
                    processing_status="pending",
                    created_by=1,
                ),
                Document(
                    name="another_doc.xliff",
                    processing_status="done",
                    created_by=1,
                ),
            ]
        )
        s.commit()

    response = user_logged_client.get("/document")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "first_doc.xliff", "status": "pending", "created_by": 1},
        {"id": 2, "name": "another_doc.xliff", "status": "done", "created_by": 1},
    ]


def test_can_get_document(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Translation",
            ),
            DocumentRecord(
                source="User Interface",
                target="UI",
            ),
        ]
        s.add(
            Document(
                name="test_doc.xliff",
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.xliff",
        "status": "pending",
        "created_by": 1,
        "records_count": 2,
    }


def test_returns_404_when_doc_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/document/1")
    assert response.status_code == 404


def test_can_delete_xliff_doc(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(
            schema.XliffDocument(
                parent_id=1,
                original_document="",
            )
        )
        s.add(
            Document(
                name="first_doc.xliff",
                processing_status="waiting",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.delete("/document/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        assert s.query(Document).count() == 0
        assert s.query(schema.XliffDocument).count() == 0


def test_returns_404_when_deleting_nonexistent_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.delete("/document/1")
    assert response.status_code == 404


def test_upload_xliff(user_logged_client: TestClient, session: Session):
    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(name="small.xliff").first()
        assert generic_doc is not None
        assert generic_doc.name == "small.xliff"
        assert generic_doc.processing_status == "uploaded"
        assert generic_doc.user.id == 1
        assert not generic_doc.records

        xliff_doc = s.query(schema.XliffDocument).filter_by(id=1).first()
        assert xliff_doc is not None
        assert xliff_doc.parent_id == generic_doc.id
        assert xliff_doc.original_document.startswith("<?xml version=")
        assert not xliff_doc.records


def test_upload_no_file(user_logged_client: TestClient):
    response = user_logged_client.post("/document/", files={})
    assert response.status_code == 422


def test_upload_removes_old_files(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(
            Document(
                name="some_doc.xliff",
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(name="some_doc.xliff").first()
        assert not doc


def test_upload_removes_only_uploaded_documents(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="uploaded_doc.xliff",
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.add(
            Document(
                name="processed_doc.xliff",
                processing_status=models.DocumentStatus.DONE.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(name="uploaded_doc.xliff").first()
        assert not doc
        doc = s.query(Document).filter_by(name="processed_doc.xliff").first()
        assert doc


def test_process_sets_document_in_pending_stage_and_creates_task_xliff(
    user_logged_client: TestClient, session: Session
):
    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "pending"


def test_process_creates_task_for_xliff(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))

    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        task = s.query(schema.DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        loaded_data["settings"] = json.loads(loaded_data["settings"])
        assert loaded_data == {
            "type": "xliff",
            "doc_id": 1,
            "settings": {
                "substitute_numbers": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
                "similarity_threshold": 1.0,
            },
        }


def test_process_creates_xliff_doc_tmx_link(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))
        s.add(schema.TmxDocument(name="another_doc.tmx", created_by=1))
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1, 2],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert len(doc.tmxs) == 2
        assert doc.tmxs[0].id == 1
        assert doc.tmxs[1].id == 2


def test_returns_404_when_processing_nonexistent_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )
    assert response.status_code == 404


def test_download_xliff_doc(user_logged_client: TestClient, session: Session):
    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    with session as s:
        records = [
            DocumentRecord(document_id=1, source="Regional Effects", target="Some"),
            DocumentRecord(document_id=1, source="Other Effects", target=""),
            DocumentRecord(
                document_id=1,
                source="Regional Effects",
                target="Региональные эффекты",
            ),
            DocumentRecord(document_id=1, source="123456789", target=""),
            schema.XliffRecord(
                parent_id=1,
                segment_id=675606,
                document_id=1,
                state="needs-translation",
                approved=False,
            ),
            schema.XliffRecord(
                parent_id=2,
                segment_id=675607,
                document_id=1,
                state="needs-translation",
                approved=True,
            ),
            schema.XliffRecord(
                parent_id=3,
                segment_id=675608,
                document_id=1,
                state="translated",
                approved=True,
            ),
            schema.XliffRecord(
                parent_id=4,
                segment_id=675609,
                document_id=1,
                state="final",
                approved=False,
            ),
        ]
        s.add_all(records)
        s.commit()

    response = user_logged_client.get("/document/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data
    assert "Региональные эффекты" in data
    assert 'approved="yes"' in data
    assert "translated" in data
    assert "final" in data


def test_download_shows_404_for_unknown_doc(user_logged_client: TestClient):
    response = user_logged_client.get("/document/1/download")
    assert response.status_code == 404
