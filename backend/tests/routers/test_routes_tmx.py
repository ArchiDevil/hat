from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord

# pylint: disable=C0116


def test_can_return_list_of_tmx_docs(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.get("/tmx/")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "first_doc.tmx",
            "created_by": 1,
        },
        {
            "id": 2,
            "name": "another_doc.tmx",
            "created_by": 1,
        },
    ]


def test_can_get_tmx_file(user_logged_client: TestClient, session: Session):
    tmx_records = [
        TranslationMemoryRecord(source="Regional Effects", target="Translation"),
        TranslationMemoryRecord(source="User Interface", target="UI"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tmx_records, created_by=1))
        s.commit()
    response = user_logged_client.get("/tmx/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.tmx",
        "created_by": 1,
        "records_count": 2,
    }


def test_can_get_tmx_records(user_logged_client: TestClient, session: Session):
    tmx_records = [
        TranslationMemoryRecord(source="Regional Effects", target="Translation"),
        TranslationMemoryRecord(source="User Interface", target="UI"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tmx_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get("/tmx/1/records")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "source": "Regional Effects", "target": "Translation"},
        {"id": 2, "source": "User Interface", "target": "UI"},
    ]


def test_can_get_tmx_records_with_page(
    user_logged_client: TestClient, session: Session
):
    tmx_records = [
        TranslationMemoryRecord(source=f"line{x}", target=f"line{x}")
        for x in range(150)
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tmx_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get("/tmx/1/records", params={"page": "1"})
    assert response.status_code == 200
    assert len(response.json()) == 50
    assert response.json()[0] == {"id": 101, "source": "line100", "target": "line100"}


def test_tmx_records_are_empty_for_too_large_page(
    user_logged_client: TestClient, session: Session
):
    tmx_records = [
        TranslationMemoryRecord(source=f"line{x}", target=f"line{x}")
        for x in range(150)
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tmx_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get("/tmx/1/records", params={"page": "20"})
    assert response.status_code == 200
    assert response.json() == []


def test_tmx_records_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/tmx/1/records", params={"page": "2"})
    assert response.status_code == 404


def test_returns_404_when_tmx_file_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/tmx/1")
    assert response.status_code == 404


def test_can_delete_tmx_doc(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.delete("/tmx/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        doc = s.query(TranslationMemory).filter_by(id=1).first()
        assert doc is None


def test_returns_404_when_deleting_nonexistent_tmx_doc(user_logged_client: TestClient):
    response = user_logged_client.delete("/tmx/10")
    assert response.status_code == 404


def test_can_upload_tmx(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.tmx", "rb") as f:
        response = user_logged_client.post(
            "/tmx",
            files={"file": f},
        )
    assert response.status_code == 200

    with session as s:
        doc = s.query(TranslationMemory).filter_by(id=1).first()
        assert doc
        assert doc.name == "small.tmx"
        assert doc.created_by == 1
        assert len(doc.records) == 1
        assert "Handbook" in doc.records[0].source
        assert doc.records[0].creation_date == datetime(2022, 7, 3, 7, 59, 19)
        assert doc.records[0].change_date == datetime(2022, 7, 3, 7, 59, 20)


def test_shows_422_when_no_file_uploaded(user_logged_client: TestClient):
    response = user_logged_client.post("/tmx")
    assert response.status_code == 422
