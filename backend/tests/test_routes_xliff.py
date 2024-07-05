from contextlib import contextmanager
from datetime import datetime, timedelta
import json

from fastapi.testclient import TestClient

from app import schema, models
from app.db import get_db

# pylint: disable=C0116


@contextmanager
def session():
    return get_db()


def test_can_get_list_of_xliff_docs(user_logged_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="first_doc.tmx",
                original_document="",
                processing_status="pending",
                created_by=1,
            )
        )
        s.add(
            schema.XliffDocument(
                name="another_doc.tmx",
                original_document="",
                processing_status="processing",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/xliff")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "first_doc.tmx", "status": "pending", "created_by": 1},
        {"id": 2, "name": "another_doc.tmx", "status": "processing", "created_by": 1},
    ]


def test_can_get_xliff_file(user_logged_client: TestClient):
    with session() as s:
        xliff_records = [
            schema.XliffRecord(
                segment_id=8, source="Regional Effects", target="Translation"
            ),
            schema.XliffRecord(segment_id=14, source="User Interface", target="UI"),
        ]
        s.add(
            schema.XliffDocument(
                name="test_doc.xliff",
                original_document="Something",
                records=xliff_records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/xliff/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.xliff",
        "status": "pending",
        "created_by": 1,
    }


def test_can_get_xliff_records(user_logged_client: TestClient):
    with session() as s:
        xliff_records = [
            schema.XliffRecord(
                segment_id=8, source="Regional Effects", target="Translation"
            ),
            schema.XliffRecord(segment_id=14, source="User Interface", target="UI"),
        ]
        s.add(
            schema.XliffDocument(
                name="test_doc.xliff",
                original_document="Something",
                records=xliff_records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/xliff/1/records")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "segment_id": 8,
            "source": "Regional Effects",
            "target": "Translation",
        },
        {
            "id": 2,
            "segment_id": 14,
            "source": "User Interface",
            "target": "UI",
        },
    ]


def test_xliff_records_returns_second_page(user_logged_client: TestClient):
    with session() as s:
        xliff_records = [
            schema.XliffRecord(segment_id=i, source=f"line{i}", target=f"line{i}")
            for i in range(150)
        ]

        s.add(
            schema.XliffDocument(
                name="test_doc.xliff",
                original_document="Something",
                records=xliff_records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/xliff/1/records", params={"page": "2"})
    assert response.status_code == 200
    assert len(response.json()) == 50
    assert response.json()[0] == {
        "id": 101,
        "segment_id": 100,
        "source": "line100",
        "target": "line100",
    }


def test_xliff_records_returns_empty_for_too_large_page(user_logged_client: TestClient):
    with session() as s:
        xliff_records = [
            schema.XliffRecord(segment_id=i, source=f"line{i}", target=f"line{i}")
            for i in range(150)
        ]

        s.add(
            schema.XliffDocument(
                name="test_doc.xliff",
                original_document="Something",
                records=xliff_records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/xliff/1/records", params={"page": "20"})
    assert response.status_code == 200
    assert response.json() == []


def test_xliff_records_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/xliff/2/records")
    assert response.status_code == 404


async def test_returns_404_when_xliff_file_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/xliff/1")
    assert response.status_code == 404


def test_can_delete_xliff_doc(user_logged_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="first_doc.tmx",
                original_document="",
                processing_status="waiting",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.delete("/xliff/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session() as s:
        assert s.query(schema.XliffDocument).count() == 0


def test_returns_404_when_deleting_nonexistent_xliff_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.delete("/xliff/1")
    assert response.status_code == 404


def test_upload(user_logged_client: TestClient):
    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/xliff", files={"file": fp})
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(id=1).first()
        assert doc is not None
        assert doc.name == "small.xliff"
        assert doc.created_by == 1
        assert doc.processing_status == "uploaded"
        assert doc.original_document.startswith("<?xml version=")
        assert not doc.records


def test_upload_no_file(user_logged_client: TestClient):
    response = user_logged_client.post("/xliff/", files={})
    assert response.status_code == 422


def test_upload_removes_old_files(user_logged_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="some_doc.xliff",
                original_document="",
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/xliff/", files={"file": fp})
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(name="some_doc.xliff").first()
        assert not doc


def test_upload_removes_only_uploaded_documents(user_logged_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="uploaded_doc.xliff",
                original_document="",
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.add(
            schema.XliffDocument(
                name="processed_doc.xliff",
                original_document="",
                processing_status=models.DocumentStatus.DONE.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = user_logged_client.post("/xliff/", files={"file": fp})
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(name="uploaded_doc.xliff").first()
        assert not doc
        doc = (
            s.query(schema.XliffDocument).filter_by(name="processed_doc.xliff").first()
        )
        assert doc


def test_process_sets_document_in_pending_stage_and_creates_task(
    user_logged_client: TestClient,
):
    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/xliff/", files={"file": fp})

    response = user_logged_client.post(
        "/xliff/1/process",
        json={
            "substitute_numbers": False,
            "use_machine_translation": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "pending"


def test_process_creates_task(user_logged_client: TestClient):
    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/xliff/", files={"file": fp})

    response = user_logged_client.post(
        "/xliff/1/process",
        json={
            "substitute_numbers": False,
            "use_machine_translation": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session() as s:
        task = s.query(schema.DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        loaded_data["settings"] = json.loads(loaded_data["settings"])
        assert loaded_data == {
            "type": "xliff",
            "doc_id": 1,
            "settings": {
                "substitute_numbers": False,
                "use_machine_translation": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [],
                "tmx_usage": "newest",
            },
        }


def test_returns_404_when_processing_nonexistent_xliff_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.post(
        "/xliff/1/process",
        json={
            "substitute_numbers": False,
            "use_machine_translation": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )
    assert response.status_code == 404


def test_download_xliff(user_logged_client: TestClient):
    with open("tests/small.xliff", "rb") as fp:
        user_logged_client.post("/xliff", files={"file": fp})

    with session() as s:
        xliff_records = [
            schema.XliffRecord(
                segment_id=675606,
                document_id=1,
                source="Regional Effects",
                target="Some",
            ),
            schema.XliffRecord(
                segment_id=675607,
                document_id=1,
                source="Other Effects",
                target="",
            ),
            schema.XliffRecord(
                segment_id=675608,
                document_id=1,
                source="Regional Effects",
                target="Региональные эффекты",
            ),
            schema.XliffRecord(
                segment_id=675609,
                document_id=1,
                source="123456789",
                target="",
            ),
        ]
        s.add_all(xliff_records)
        s.commit()

    response = user_logged_client.get("/xliff/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data
    assert "Региональные эффекты" in data


def test_download_shows_404_for_unknown_xliff(user_logged_client: TestClient):
    response = user_logged_client.get("/xliff/1/download")
    assert response.status_code == 404
