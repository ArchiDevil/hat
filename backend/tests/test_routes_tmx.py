from contextlib import contextmanager

from fastapi.testclient import TestClient

from app import schema
from app.db_fastapi import get_db


@contextmanager
def session():
    return get_db()


def test_can_return_list_of_tmx_docs(fastapi_client: TestClient):
    with session() as s:
        s.add(schema.TmxDocument(name="first_doc.tmx"))
        s.add(schema.TmxDocument(name="another_doc.tmx"))
        s.commit()

    response = fastapi_client.get("/tmx/")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "first_doc.tmx",
        },
        {
            "id": 2,
            "name": "another_doc.tmx",
        },
    ]


def test_can_get_tmx_file(fastapi_client: TestClient):
    tmx_records = [
        schema.TmxRecord(source="Regional Effects", target="Translation"),
        schema.TmxRecord(source="User Interface", target="UI"),
    ]
    with session() as s:
        s.add(schema.TmxDocument(name="test_doc.tmx", records=tmx_records))
        s.commit()

    response = fastapi_client.get("/tmx/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.tmx",
        "records": [
            {
                "id": 1,
                "source": "Regional Effects",
                "target": "Translation",
            },
            {
                "id": 2,
                "source": "User Interface",
                "target": "UI",
            },
        ],
    }


def test_returns_404_when_tmx_file_not_found(fastapi_client: TestClient):
    response = fastapi_client.get("/tmx/1")
    assert response.status_code == 404


def test_can_delete_tmx_doc(fastapi_client: TestClient):
    with session() as s:
        s.add(schema.TmxDocument(name="first_doc.tmx"))
        s.commit()

    response = fastapi_client.delete("/tmx/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session() as s:
        doc = s.query(schema.TmxDocument).filter_by(id=1).first()
        assert doc is None


def test_returns_404_when_deleting_nonexistent_tmx_doc(fastapi_client: TestClient):
    response = fastapi_client.post("/tmx/1/delete")
    assert response.status_code == 404


def test_can_upload_tmx(fastapi_client: TestClient):
    with open("tests/small.tmx", "rb") as f:
        response = fastapi_client.post(
            "/tmx",
            files={"file": f},
        )
    assert response.status_code == 200

    with session() as s:
        doc = s.query(schema.TmxDocument).filter_by(id=1).first()
        assert doc
        assert doc.name == "small.tmx"
        assert len(doc.records) == 1
        assert "Handbook" in doc.records[0].source


def test_shows_422_when_no_file_uploaded(fastapi_client: TestClient):
    response = fastapi_client.post("/tmx")
    assert response.status_code == 422
