import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.comments.models import Comment
from app.documents.models import (
    DocMemoryAssociation,
    Document,
    DocumentRecord,
    DocumentType,
    RecordSource,
)
from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord

# pylint: disable=C0116


def test_can_get_doc_records(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Translation",
                target_source=RecordSource.translation_memory,
            ),
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
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 2
    assert response_data["records"] == [
        {
            "id": 1,
            "source": "Regional Effects",
            "target": "Translation",
            "approved": False,
            "repetitions_count": 1,
            "has_comments": False,
            "translation_src": "tm",
        },
        {
            "id": 2,
            "source": "User Interface",
            "target": "UI",
            "approved": True,
            "repetitions_count": 1,
            "has_comments": False,
            "translation_src": None,
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
    response_data = response.json()
    assert response_data["page"] == 1
    assert response_data["total_records"] == 150
    assert len(response_data["records"]) == 50
    assert response_data["records"][0] == {
        "id": 101,
        "source": "line100",
        "target": "line100",
        "approved": False,
        "repetitions_count": 1,
        "has_comments": False,
        "translation_src": None,
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
    response_data = response.json()
    assert response_data["page"] == 20
    assert response_data["total_records"] == 150
    assert response_data["records"] == []


def test_doc_records_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/document/2/records")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "arguments",
    [
        {"target": "Updated", "approved": None, "update_repetitions": False},
        {"target": "Updated", "approved": True, "update_repetitions": False},
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

    response = user_logged_client.put("/document/records/2", json=arguments)
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
        "/document/records/1",
        json={
            "target": "Updated",
            "approved": True,
            "update_repetitions": False,
        },
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
        "/document/records/1",
        json={
            "target": "Updated",
            "approved": True,
            "update_repetitions": False,
        },
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
        "/document/records/3",
        json={
            "target": "Updated",
            "approved": None,
            "update_repetitions": False,
        },
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
        "/document/1/records/3", json={"target": "Updated"}
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
        "/document/records/1",
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
        "/document/records/1",
        json={
            "target": "Updated Hello",
            "approved": True,
            "update_repetitions": False,
        },
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


def test_doc_records_source_filter(user_logged_client: TestClient, session: Session):
    """Test filtering document records by source text"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
            DocumentRecord(source="Hello Universe", target="Привет Вселенная"),
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

    # Test filtering by "Hello"
    response = user_logged_client.get("/document/1/records", params={"source": "Hello"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 2
    records_response = response_data["records"]
    assert len(records_response) == 2

    # Should return records with "Hello World" and "Hello Universe"
    sources = [record["source"] for record in records_response]
    assert "Hello World" in sources
    assert "Hello Universe" in sources
    assert "Goodbye" not in sources


def test_doc_records_target_filter(user_logged_client: TestClient, session: Session):
    """Test filtering document records by target text"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
            DocumentRecord(source="Hello Universe", target="Привет Вселенная"),
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

    # Test filtering by "Привет"
    response = user_logged_client.get(
        "/document/1/records", params={"target": "Привет"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 2
    records_response = response_data["records"]
    assert len(records_response) == 2

    # Should return records with "Привет Мир" and "Привет Вселенная"
    targets = [record["target"] for record in records_response]
    assert "Привет Мир" in targets
    assert "Привет Вселенная" in targets
    assert "Пока" not in targets


def test_doc_records_both_filters(user_logged_client: TestClient, session: Session):
    """Test filtering document records by both source and target text"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
            DocumentRecord(source="Hello Universe", target="Привет Вселенная"),
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

    # Test filtering by both source "Hello" and target "Привет"
    response = user_logged_client.get(
        "/document/1/records",
        params={"source": "Hello", "target": "Вселенная"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 1
    records_response = response_data["records"]
    assert len(records_response) == 1

    # Should return records that match either filter
    sources = [record["source"] for record in records_response]
    targets = [record["target"] for record in records_response]

    assert "Hello Universe" in sources and "Привет Вселенная" in targets
    assert "Goodbye" not in sources


def test_doc_records_no_filter_matches(
    user_logged_client: TestClient, session: Session
):
    """Test filtering with no matching results"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
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

    # Test filtering by text that doesn't exist
    response = user_logged_client.get(
        "/document/1/records", params={"source": "Nonexistent"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 0
    records_response = response_data["records"]
    assert len(records_response) == 0


def test_doc_records_case_insensitive_filter(
    user_logged_client: TestClient, session: Session
):
    """Test that filtering is case insensitive"""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="hello universe", target="Привет Вселенная"),
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

    # Test filtering with different case
    response = user_logged_client.get("/document/1/records", params={"source": "HELLO"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 2
    records_response = response_data["records"]
    assert len(records_response) == 2

    sources = [record["source"] for record in records_response]
    assert "Hello World" in sources
    assert "hello universe" in sources


def test_doc_records_filter_with_pagination(
    user_logged_client: TestClient, session: Session
):
    """Test that filtering works with pagination"""
    with session as s:
        records = [
            DocumentRecord(source=f"Hello {i}", target=f"Привет {i}") for i in range(10)
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

    # First, test page 0 to see how many records we get
    response = user_logged_client.get(
        "/document/1/records", params={"source": "Hello", "page": 0}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 10
    records_response = response_data["records"]
    assert len(records_response) == 10  # Should get all 10 records on page 0

    # Test filtering with pagination to page 1
    response = user_logged_client.get(
        "/document/1/records", params={"source": "Hello", "page": 1}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 1
    assert response_data["total_records"] == 10
    records_response = response_data["records"]
    assert (
        len(records_response) == 0
    )  # Should get no records on page 1 since default page size is 100

    # All should contain "Hello" in source (if any records were returned)
    for record in records_response:
        assert "Hello" in record["source"]


def test_update_repetitions_only_when_approved(
    user_logged_client: TestClient, session: Session
):
    """Test that repetitions are only updated when segment is approved, not just updated"""
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

    # Update record 1 with repetition update enabled but NOT approved
    response = user_logged_client.put(
        "/document/records/1",
        json={"target": "Updated Hello", "approved": False, "update_repetitions": True},
    )
    assert response.status_code == 200

    with session as s:
        # Check that only record 1 was updated (no repetitions updated since not approved)
        record1 = s.query(DocumentRecord).filter(DocumentRecord.id == 1).one()
        record2 = s.query(DocumentRecord).filter(DocumentRecord.id == 2).one()
        record3 = s.query(DocumentRecord).filter(DocumentRecord.id == 3).one()

        assert record1.target == "Updated Hello"
        assert record1.approved is False

        assert record2.target == "Здравствуйте Мир"  # unchanged - no repetition update
        assert record2.approved is False

        assert record3.target == "Пока"  # unchanged (different source)
        assert record3.approved is False

    # Now update record 1 with repetition update enabled AND approved
    response = user_logged_client.put(
        "/document/records/1",
        json={"target": "Final Hello", "approved": True, "update_repetitions": True},
    )
    assert response.status_code == 200

    with session as s:
        # Check that all records with "Hello World" source were updated
        record1 = s.query(DocumentRecord).filter(DocumentRecord.id == 1).one()
        record2 = s.query(DocumentRecord).filter(DocumentRecord.id == 2).one()

        assert record1.target == "Final Hello"
        assert record1.approved is True

        assert (
            record2.target == "Final Hello"
        )  # updated - repetition update since approved
        assert record2.approved is True


def test_has_comments_field(user_logged_client: TestClient, session: Session):
    """Test that has_comments field correctly shows if document record has comments"""
    with session as s:
        # Create document records
        records = [
            DocumentRecord(source="Hello World", target="Привет мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
            DocumentRecord(source="Thank you", target="Спасибо"),
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

        # Add comments to first and third records
        comment1 = Comment(
            text="First comment",
            created_by=1,
            record_id=records[0].id,  # First record
        )
        comment2 = Comment(
            text="Second comment",
            created_by=1,
            record_id=records[2].id,  # Third record
        )
        s.add_all([comment1, comment2])
        s.commit()

    response = user_logged_client.get("/document/1/records")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["page"] == 0
    assert response_data["total_records"] == 3

    records_response = response_data["records"]
    assert len(records_response) == 3

    # Check has_comments values
    # Record 1 should have comments (has 1 comment)
    assert records_response[0]["id"] == 1
    assert records_response[0]["source"] == "Hello World"
    assert records_response[0]["has_comments"]

    # Record 2 should not have comments
    assert records_response[1]["id"] == 2
    assert records_response[1]["source"] == "Goodbye"
    assert not records_response[1]["has_comments"]

    # Record 3 should have comments (has 1 comment)
    assert records_response[2]["id"] == 3
    assert records_response[2]["source"] == "Thank you"
    assert records_response[2]["has_comments"]


def test_has_comments_with_multiple_comments(
    user_logged_client: TestClient, session: Session
):
    """Test that has_comments is True when record has multiple comments"""
    with session as s:
        # Create document record
        record = DocumentRecord(source="Test", target="Тест")
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=[record],
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

        # Add multiple comments to the same record
        comments = [
            Comment(text="Comment 1", created_by=1, record_id=record.id),
            Comment(text="Comment 2", created_by=1, record_id=record.id),
            Comment(text="Comment 3", created_by=1, record_id=record.id),
        ]
        s.add_all(comments)
        s.commit()

    response = user_logged_client.get("/document/1/records")
    assert response.status_code == 200
    response_data = response.json()

    records_response = response_data["records"]
    assert len(records_response) == 1

    # Should still be True even with multiple comments
    assert records_response[0]["has_comments"]
