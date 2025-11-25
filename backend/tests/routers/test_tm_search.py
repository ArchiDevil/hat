from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import (
    DocMemoryAssociation,
    Document,
    DocumentType,
    TmMode,
)
from app.translation_memory.models import TranslationMemory, TranslationMemoryRecord


def test_search_tm_exact_with_no_linked_memories(
    user_logged_client: TestClient, session: Session
):
    """Test exact search returns empty response when document has no linked TMs"""
    with session as s:
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/tm/exact?source=Hello")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["records"] == []
    assert response_json["page"] == 0
    assert response_json["total_records"] == 0


def test_search_tm_exact_with_linked_memories(
    user_logged_client: TestClient, session: Session
):
    """Test exact search finds matches in linked translation memories"""
    with session as s:
        # Create document
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                processing_status="pending",
                created_by=1,
            )
        )

        # Create translation memory with records
        tm = TranslationMemory(name="test_memory.tmx", created_by=1)
        s.add(tm)
        s.flush()

        # Add some records to TM
        s.add_all(
            [
                TranslationMemoryRecord(
                    document_id=tm.id,
                    source="Hello World",
                    target="Привет Мир",
                ),
                TranslationMemoryRecord(
                    document_id=tm.id,
                    source="Goodbye",
                    target="Пока",
                ),
                TranslationMemoryRecord(
                    document_id=tm.id,
                    source="Hello Again",
                    target="Привет снова",
                ),
            ]
        )

        # Link TM to document
        s.add(DocMemoryAssociation(doc_id=1, tm_id=tm.id, mode=TmMode.read))
        s.commit()

    # Test exact search for "Hello"
    response = user_logged_client.get("/document/1/tm/exact?source=Hello")
    assert response.status_code == 200
    response_json = response.json()
    assert (
        len(response_json["records"]) == 2
    )  # Should find "Hello World" and "Hello Again"
    assert response_json["page"] == 0
    assert response_json["total_records"] == 2

    # Check the returned records
    sources = [record["source"] for record in response_json["records"]]
    assert "Hello World" in sources
    assert "Hello Again" in sources


def test_search_tm_exact_with_multiple_linked_memories(
    user_logged_client: TestClient, session: Session
):
    """Test exact search across multiple linked translation memories"""
    with session as s:
        # Create document
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                processing_status="pending",
                created_by=1,
            )
        )

        # Create two translation memories
        tm1 = TranslationMemory(name="memory1.tmx", created_by=1)
        tm2 = TranslationMemory(name="memory2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.flush()

        # Add records to both TMs
        s.add_all(
            [
                TranslationMemoryRecord(
                    document_id=tm1.id,
                    source="Hello World",
                    target="Привет Мир",
                ),
                TranslationMemoryRecord(
                    document_id=tm2.id,
                    source="Hello Again",
                    target="Привет снова",
                ),
                TranslationMemoryRecord(
                    document_id=tm2.id,
                    source="Goodbye",
                    target="Пока",
                ),
            ]
        )

        # Link both TMs to document
        s.add(DocMemoryAssociation(doc_id=1, tm_id=tm1.id, mode=TmMode.read))
        s.add(DocMemoryAssociation(doc_id=1, tm_id=tm2.id, mode=TmMode.read))
        s.commit()

    # Test exact search for "Hello"
    response = user_logged_client.get("/document/1/tm/exact?source=Hello")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json["records"]) == 2  # Should find from both TMs
    assert response_json["page"] == 0
    assert response_json["total_records"] == 2


def test_search_tm_exact_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    """Test exact search returns 404 for non-existent document"""
    response = user_logged_client.get("/document/999/tm/exact?source=Hello")
    assert response.status_code == 404


def test_search_tm_exact_no_results(user_logged_client: TestClient, session: Session):
    """Test exact search returns no results when no matches found"""
    with session as s:
        # Create document
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                processing_status="pending",
                created_by=1,
            )
        )

        # Create TM with different records
        tm = TranslationMemory(name="test_memory.tmx", created_by=1)
        s.add(tm)
        s.flush()

        s.add(
            TranslationMemoryRecord(
                document_id=tm.id,
                source="Goodbye World",
                target="Пока Мир",
            )
        )

        # Link TM to document
        s.add(DocMemoryAssociation(doc_id=1, tm_id=tm.id, mode=TmMode.read))
        s.commit()

    # Test exact search for "Hello" (should not find anything)
    response = user_logged_client.get("/document/1/tm/exact?source=Hello")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["records"] == []
    assert response_json["page"] == 0
    assert response_json["total_records"] == 0


def test_search_tm_limit_20_results(user_logged_client: TestClient, session: Session):
    """Test that search endpoints limit results to 20 records"""
    with session as s:
        # Create document
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                processing_status="pending",
                created_by=1,
            )
        )

        # Create TM
        tm = TranslationMemory(name="test_memory.tmx", created_by=1)
        s.add(tm)
        s.flush()

        # Add 25 records starting with "Hello"
        s.add_all(
            [
                TranslationMemoryRecord(
                    document_id=tm.id,
                    source=f"Hello World {i}",
                    target=f"Привет Мир {i}",
                )
                for i in range(25)
            ]
        )

        # Link TM to document
        s.add(DocMemoryAssociation(doc_id=1, tm_id=tm.id, mode=TmMode.read))
        s.commit()

    # Test exact search - should only return 20 results
    response = user_logged_client.get("/document/1/tm/exact?source=Hello")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json["records"]) == 20  # Limited to 20
