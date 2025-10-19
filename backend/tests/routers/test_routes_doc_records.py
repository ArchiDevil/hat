import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import (
    DocMemoryAssociation,
    Document,
    DocumentRecord,
    DocumentType,
)
from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord

# pylint: disable=C0116


def test_can_get_doc_records(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(source="Regional Effects", target="Translation"),
            DocumentRecord(source="User Interface", target="UI", approved=True),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/records")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "source": "Regional Effects",
            "target": "Translation",
            "approved": False,
            "repetitions_count": 1,
        },
        {
            "id": 2,
            "source": "User Interface",
            "target": "UI",
            "approved": True,
            "repetitions_count": 1,
        },
    ]


def test_doc_records_returns_second_page(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(
                source=f"line{i}",
                target=f"line{i}",
            )
            for i in range(150)
        ]

        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/records", params={"page": "1"})
    assert response.status_code == 200
    assert len(response.json()) == 50
    assert response.json()[0] == {
        "id": 101,
        "source": "line100",
        "target": "line100",
        "approved": False,
        "repetitions_count": 1,
    }


def test_doc_records_returns_empty_for_too_large_page(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(
                source=f"line{i}",
                target=f"line{i}",
            )
            for i in range(150)
        ]

        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/records", params={"page": "20"})
    assert response.status_code == 200
    assert response.json() == []


def test_doc_records_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/document/2/records")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "arguments",
    [
        {"target": "Updated", "approved": None},
        {"target": "Updated", "approved": True},
    ],
)
def test_can_update_doc_record(
    user_logged_client: TestClient, session: Session, arguments: dict[str, str]
):
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
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.put("/document/record/2", json=arguments)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": 2,
        "source": "User Interface",
        "target": "Updated",
        "approved": arguments["approved"] or False,
    }

    with session as s:
        record = s.query(DocumentRecord).filter(DocumentRecord.id == 2).one()
        assert (record.target == arguments["target"]) if arguments["target"] else True
        assert (
            (record.approved == arguments["approved"])
            if arguments["approved"]
            else True
        )


def test_record_approving_creates_memory(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Some source", target=""),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.add(
            TranslationMemory(
                name="test_mem",
                created_by=1,
            )
        )
        s.commit()

        s.add(DocMemoryAssociation(doc_id=1, tm_id=1, mode="write"))
        s.commit()

    response = user_logged_client.put(
        "/document/record/1", json={"target": "Updated", "approved": True}
    )
    assert response.status_code == 200, response.text

    with session as s:
        record = (
            s.query(TranslationMemoryRecord)
            .filter(TranslationMemoryRecord.id == 1)
            .one()
        )
        assert record.source == "Some source"
        assert record.target == "Updated"
        assert record.document_id == 1

        today = datetime.datetime.now(datetime.UTC)
        assert record.creation_date.date() == today.date()
        assert record.change_date.date() == today.date()


def test_record_approving_updates_memory(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Some source", target=""),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        tm_records = [
            TranslationMemoryRecord(
                source="Some source",
                target="Old target",
                creation_date=datetime.datetime(2000, 4, 5),
                change_date=datetime.datetime(2000, 4, 6),
            ),
        ]
        s.add(TranslationMemory(name="test_mem", created_by=1, records=tm_records))
        s.commit()

        s.add(DocMemoryAssociation(doc_id=1, tm_id=1, mode="write"))
        s.commit()

    response = user_logged_client.put(
        "/document/record/1", json={"target": "Updated", "approved": True}
    )
    assert response.status_code == 200, response.text

    with session as s:
        record = (
            s.query(TranslationMemoryRecord)
            .filter(TranslationMemoryRecord.id == 1)
            .one()
        )
        assert record.source == "Some source"
        assert record.target == "Updated"
        assert record.document_id == 1

        today = datetime.datetime.now(datetime.UTC)
        assert record.creation_date.date() == datetime.datetime(2000, 4, 5).date()
        assert record.change_date.date() == today.date()


def test_returns_404_for_nonexistent_doc_when_updating_record(
    user_logged_client: TestClient,
):
    response = user_logged_client.put(
        "/document/record/3", json={"target": "Updated", "approved": None}
    )
    assert response.status_code == 404


def test_returns_404_for_nonexistent_record(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=[],
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.put(
        "/document/1/record/3", json={"target": "Updated"}
    )
    assert response.status_code == 404


def test_can_update_doc_record_with_repetitions(
    user_logged_client: TestClient, session: Session
):
    """Test updating all records with the same source text"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Hello World", target="Здравствуйте Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    # Update record 1 with repetition update enabled
    response = user_logged_client.put(
        "/document/record/1",
        json={"target": "Updated Hello", "approved": True, "update_repetitions": True},
    )
    assert response.status_code == 200

    with session as s:
        # Check that all records with "Hello World" source were updated
        record1 = s.query(DocumentRecord).filter(DocumentRecord.id == 1).one()
        record2 = s.query(DocumentRecord).filter(DocumentRecord.id == 2).one()
        record3 = s.query(DocumentRecord).filter(DocumentRecord.id == 3).one()

        assert record1.target == "Updated Hello"
        assert record1.approved is True

        assert record2.target == "Updated Hello"  # updated
        assert record2.approved is True

        assert record3.target == "Пока"  # unchanged (different source)
        assert record3.approved is False


def test_update_repetitions_default_behavior(
    user_logged_client: TestClient, session: Session
):
    """Test that update_repetitions defaults to False when not specified"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Hello World", target="Здравствуйте Мир"),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    # Update without specifying update_repetitions (should default to False)
    response = user_logged_client.put(
        "/document/record/1", json={"target": "Updated Hello", "approved": True}
    )
    assert response.status_code == 200

    with session as s:
        # Check that only record 1 was updated
        record1 = s.query(DocumentRecord).filter(DocumentRecord.id == 1).one()
        record2 = s.query(DocumentRecord).filter(DocumentRecord.id == 2).one()

        assert record1.target == "Updated Hello"
        assert record1.approved is True

        assert record2.target == "Здравствуйте Мир"  # unchanged
        assert record2.approved is False
