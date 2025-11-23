from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord

# pylint: disable=C0116


def test_can_return_list_of_tm_docs(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.get("/translation_memory/")
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


def test_can_get_tm_file(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source="Regional Effects", target="Translation"),
        TranslationMemoryRecord(source="User Interface", target="UI"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()
    response = user_logged_client.get("/translation_memory/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.tmx",
        "created_by": 1,
        "records_count": 2,
    }


def test_can_get_tm_records(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source="Regional Effects", target="Translation"),
        TranslationMemoryRecord(source="User Interface", target="UI"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get("/translation_memory/1/records")
    assert response.status_code == 200
    assert response.json() == {
        "records": [
            {"id": 1, "source": "Regional Effects", "target": "Translation"},
            {"id": 2, "source": "User Interface", "target": "UI"},
        ],
        "page": 0,
        "total_records": 2,
    }


def test_can_get_tm_records_with_page(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source=f"line{x}", target=f"line{x}")
        for x in range(150)
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get(
        "/translation_memory/1/records", params={"page": "1"}
    )
    assert response.status_code == 200
    json = response.json()
    assert len(json["records"]) == 50
    assert json["records"][0] == {"id": 101, "source": "line100", "target": "line100"}


def test_tm_records_are_empty_for_too_large_page(
    user_logged_client: TestClient, session: Session
):
    tm_records = [
        TranslationMemoryRecord(source=f"line{x}", target=f"line{x}")
        for x in range(150)
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    with session as s:
        docs = s.query(TranslationMemory).all()
        assert len(docs) == 1

    response = user_logged_client.get(
        "/translation_memory/1/records", params={"page": "20"}
    )
    assert response.status_code == 200
    assert response.json()["records"] == []


def test_tm_records_exact_match(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source="Hello world", target="Hola mundo"),
        TranslationMemoryRecord(source="Goodbye world", target="Adiós mundo"),
        TranslationMemoryRecord(source="Welcome home", target="Bienvenido a casa"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    # Test exact search for "world"
    response = user_logged_client.get(
        "/translation_memory/1/records",
        params={"query": "world", "query_mode": "exact"},
    )
    assert response.status_code == 200

    json = response.json()
    assert len(json["records"]) == 2
    assert json["total_records"] == 2
    # Should return records containing "world" in source
    sources = [result["source"] for result in json["records"]]
    assert "Hello world" in sources
    assert "Goodbye world" in sources
    # Similarity should be None for exact search
    assert all("similarity" not in result for result in json["records"])


def test_tm_records_exact_match_in_nonexistent_tm(user_logged_client: TestClient):
    response = user_logged_client.get(
        "/translation_memory/999/records",
        params={"query": "test", "query_mode": "exact"},
    )
    assert response.status_code == 404
    assert "Memory not found" in response.json()["detail"]


def test_search_no_results(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source="Hello world", target="Hola mundo"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    # Search for something that doesn't exist
    response = user_logged_client.get(
        "/translation_memory/1/records",
        params={"query": "nonexistent", "query_mode": "exact"},
    )
    assert response.status_code == 200

    results = response.json()["records"]
    assert len(results) == 0


def test_tm_records_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get(
        "/translation_memory/1/records", params={"page": "2"}
    )
    assert response.status_code == 404


def test_returns_404_when_tm_file_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/translation_memory/1")
    assert response.status_code == 404


def test_can_delete_tm_doc(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.delete("/translation_memory/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        doc = s.query(TranslationMemory).filter_by(id=1).first()
        assert doc is None


def test_returns_404_when_deleting_nonexistent_tm_doc(user_logged_client: TestClient):
    response = user_logged_client.delete("/translation_memory/10")
    assert response.status_code == 404


def test_can_upload_tm(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.tmx", "rb") as f:
        response = user_logged_client.post(
            "/translation_memory/upload",
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
    response = user_logged_client.post("/translation_memory/upload")
    assert response.status_code == 422


def test_can_create_tm(user_logged_client: TestClient, session: Session):
    response = user_logged_client.post(
        "/translation_memory",
        json={"name": "test"},
    )

    assert response.status_code == 201

    with session as s:
        tm = s.query(TranslationMemory).filter_by(id=response.json()["id"]).first()
        assert tm
        assert tm.name == "test"
        assert tm.created_by == 1
        assert len(tm.records) == 0


def test_can_download_document(user_logged_client: TestClient, session: Session):
    tm_records = [
        TranslationMemoryRecord(source="Regional Effects", target="Translation"),
        TranslationMemoryRecord(source="User Interface", target="UI"),
    ]
    with session as s:
        s.add(TranslationMemory(name="test_doc.tmx", records=tm_records, created_by=1))
        s.commit()

    response = user_logged_client.get("/translation_memory/1/download")
    assert response.status_code == 200
    data = response.read().decode("utf-8")
    assert "Regional Effects" in data
    assert "Translation" in data
    assert "User Interface" in data
    assert "UI" in data


def test_download_returns_404_for_non_existing_tm(user_logged_client: TestClient):
    response = user_logged_client.get("/translation_memory/999/download")
    assert response.status_code == 404
