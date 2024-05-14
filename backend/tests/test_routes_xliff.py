from contextlib import contextmanager

from fastapi.testclient import TestClient

from app import schema
from app.db import get_db


@contextmanager
def session():
    return get_db()


def test_can_get_list_of_xliff_docs(fastapi_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="first_doc.tmx", original_document="", processing_status="pending"
            )
        )
        s.add(
            schema.XliffDocument(
                name="another_doc.tmx",
                original_document="",
                processing_status="processing",
            )
        )
        s.commit()

    response = fastapi_client.get("/xliff")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "first_doc.tmx", "status": "pending"},
        {"id": 2, "name": "another_doc.tmx", "status": "processing"},
    ]


def test_can_get_xliff_file(fastapi_client: TestClient):
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
            )
        )
        s.commit()

    response = fastapi_client.get("/xliff/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.xliff",
        "status": "pending",
    }


def test_can_get_xliff_records(fastapi_client: TestClient):
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
            )
        )
        s.commit()

    response = fastapi_client.get("/xliff/1/records")
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


async def test_returns_404_when_xliff_file_not_found(fastapi_client: TestClient):
    response = fastapi_client.get("/xliff/1")
    assert response.status_code == 404


def test_can_delete_xliff_doc(fastapi_client: TestClient):
    with session() as s:
        s.add(
            schema.XliffDocument(
                name="first_doc.tmx", original_document="", processing_status="waiting"
            )
        )
        s.commit()

    response = fastapi_client.delete("/xliff/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session() as s:
        assert s.query(schema.XliffDocument).count() == 0


def test_returns_404_when_deleting_nonexistent_xliff_doc(fastapi_client: TestClient):
    response = fastapi_client.delete("/xliff/1")
    assert response.status_code == 404


def test_upload(fastapi_client: TestClient):
    with open("tests/small.xliff", "rb") as fp:
        response = fastapi_client.post("/xliff", files={"file": fp})
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(id=1).first()
        assert doc is not None
        assert doc.name == "small.xliff"
        assert doc.processing_status == "uploaded"
        assert doc.original_document.startswith("<?xml version=")
        assert not doc.records


def test_upload_no_file(fastapi_client: TestClient):
    response = fastapi_client.post("/xliff/", files={})
    assert response.status_code == 422


def test_process_sets_records(fastapi_client: TestClient):
    with session() as s:
        tmx_records = [
            schema.TmxRecord(source="Regional Effects", target="Translation")
        ]
        s.add(schema.TmxDocument(name="test", records=tmx_records))
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        fastapi_client.post("/xliff", files={"file": fp})

    response = fastapi_client.post(
        "/xliff/1/process", json={"substitute_numbers": False}
    )
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
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


def test_process_substitutes_numbers(fastapi_client: TestClient):
    with session() as s:
        tmx_records = []
        s.add(schema.TmxDocument(name="test", records=tmx_records))
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        fastapi_client.post("/xliff", files={"file": fp})

    response = fastapi_client.post(
        "/xliff/1/process", json={"substitute_numbers": True}
    )
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.XliffDocument).filter_by(id=1).one()
        assert doc.processing_status == "done"
        assert len(doc.records) == 4
        # It substitutes numbers
        assert doc.records[3].id == 4
        assert doc.records[3].segment_id == 675609
        assert doc.records[3].document_id == 1
        assert doc.records[3].source == "123456789"
        assert doc.records[3].target == "123456789"


def test_returns_404_when_processing_nonexistent_xliff_doc(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/xliff/1/process", json={"substitute_numbers": False}
    )
    assert response.status_code == 404


def test_download_xliff(fastapi_client: TestClient):
    with session() as s:
        tmx_records = [
            schema.TmxRecord(source="Regional Effects", target="RegEffectsTranslation")
        ]
        s.add(schema.TmxDocument(name="test", records=tmx_records))
        s.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = fastapi_client.post("/xliff", files={"file": fp})

    response = fastapi_client.get("/xliff/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "RegEffectsTranslation" in data


def test_download_shows_404_for_unknown_xliff(fastapi_client: TestClient):
    response = fastapi_client.get("/xliff/1/download")
    assert response.status_code == 404
