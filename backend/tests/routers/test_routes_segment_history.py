"""Tests for segment history tracking functionality."""

import json
from datetime import UTC, datetime, timedelta
from time import sleep

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentRecordHistory,
    DocumentRecordHistoryChangeType,
    DocumentType,
)
from app.documents.utils import apply_diff, compute_diff


def test_get_segment_history_empty(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Test translation"),
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

    response = user_logged_client.get("/document/records/1/history")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["history"] == []


def test_get_segment_history_with_entries(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Test translation"),
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
        s.flush()

        # Add history entries with JSON diff format
        diff1 = compute_diff("Test translation", "new")
        diff2 = compute_diff("Test translation", "old")
        history1 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff1,
            author_id=1,  # Use ID 1 which will be the test user
            change_type=DocumentRecordHistoryChangeType.manual_edit,
            timestamp=datetime.now(UTC) - timedelta(minutes=1),
        )
        history2 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff2,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.machine_translation,
            timestamp=datetime.now(UTC) - timedelta(minutes=5),
        )
        s.add_all([history1, history2])
        s.commit()

        # Store IDs before session closes
        history1_id = history1.id
        history2_id = history2.id

    response = user_logged_client.get("/document/records/1/history")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["history"]) == 2

    # Check that history is ordered by timestamp (newest first)
    assert response_data["history"][0]["change_type"] == "manual_edit"
    assert response_data["history"][1]["change_type"] == "machine_translation"

    # Check first history entry (manual_edit)
    assert response_data["history"][0]["id"] == history1_id
    # Verify diff is valid JSON
    diff1_data = json.loads(response_data["history"][0]["diff"])
    assert "ops" in diff1_data
    assert "old_len" in diff1_data
    assert response_data["history"][0]["author"]["id"] == 1
    assert response_data["history"][0]["author"]["username"] == "test"

    # Check second history entry (machine_translation)
    assert response_data["history"][1]["id"] == history2_id
    # Verify diff is valid JSON
    diff2_data = json.loads(response_data["history"][1]["diff"])
    assert "ops" in diff2_data
    assert "old_len" in diff2_data
    assert response_data["history"][1]["author"] is None


def test_get_segment_history_404_for_nonexistent_record(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/document/records/999/history")
    assert response.status_code == 404


def test_update_record_creates_history(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=[
                    DocumentRecord(source="Hello World", target="Test translation"),
                ],
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    # Update record
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Updated translation",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that history was created
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .all()
        )
        assert len(history) == 1
        assert history[0].change_type == DocumentRecordHistoryChangeType.manual_edit
        assert history[0].author_id == 1


def test_update_record_with_repetitions_creates_history(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=[
                    DocumentRecord(source="Hello World", target="Test translation"),
                    DocumentRecord(source="Hello World", target=""),
                    DocumentRecord(source="No hello world", target=" translation"),
                ],
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    # Update record
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Updated translation",
            "approved": True,
            "update_repetitions": True,
        },
    )
    assert response.status_code == 200

    # Check that history was created
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .one()
        )
        assert history.change_type == DocumentRecordHistoryChangeType.manual_edit
        assert history.author_id == 1

        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 2)
            .one()
        )
        assert history.change_type == DocumentRecordHistoryChangeType.repetition
        assert history.author_id == 1

        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 3)
            .all()
        )
        assert history == []


def test_update_same_type_updates_in_place(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(
                source="Hello World", target="Test translation", approved=False
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
        s.flush()

        # Create initial history entry with JSON diff format
        initial_diff = compute_diff("Test translation", "first")
        initial_history = DocumentRecordHistory(
            record_id=records[0].id,
            diff=initial_diff,
            author_id=1,
            change_type=DocumentRecordHistoryChangeType.manual_edit,
        )
        s.add(initial_history)
        s.commit()

        # Store ID before session closes
        initial_history_id = initial_history.id

    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Updated first",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that only one history entry exists (updated in-place)
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .all()
        )
        assert len(history) == 1
        assert history[0].id == initial_history_id
        assert history[0].diff is not None
        diff_data = json.loads(history[0].diff)
        assert "ops" in diff_data
        assert "old_len" in diff_data


def test_update_different_type_creates_new_history(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(
                source="Hello World", target="Test translation", approved=True
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
        s.flush()

        # Create initial history entry with JSON diff format
        initial_diff = compute_diff("Test translation", "first")
        initial_history = DocumentRecordHistory(
            record_id=records[0].id,
            diff=initial_diff,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.glossary_substitution,
            timestamp=datetime.now(UTC) - timedelta(minutes=1),
        )
        s.add(initial_history)
        s.commit()

    # Update approved record with different target text
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Updated translation",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that a new history entry was created
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .order_by(DocumentRecordHistory.timestamp.desc())
            .all()
        )
        assert len(history) == 2
        assert history[0].diff is not None
        assert history[0].change_type == DocumentRecordHistoryChangeType.manual_edit


def test_history_cascade_delete_on_record_delete(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Test translation"),
        ]
        doc = Document(
            name="test_doc.txt",
            type=DocumentType.txt,
            records=records,
            processing_status="pending",
            created_by=1,
        )
        s.add(doc)
        s.flush()

        # Add history entries with JSON diff format
        diff1 = compute_diff("Test translation", "diff1")
        diff2 = compute_diff("Test translation", "diff2")
        history1 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff1,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.manual_edit,
        )
        history2 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff2,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.machine_translation,
        )
        s.add_all([history1, history2])
        s.commit()

    # Delete document
    response = user_logged_client.delete("/document/1")
    assert response.status_code == 200

    # Check that history was cascade deleted
    with session as s:
        history = s.query(DocumentRecordHistory).all()
        assert len(history) == 0


def test_no_history_for_same_text(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Same text"),
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

    # Update with same text but different approval status
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Same text",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that history was not created (due to approval change)
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .all()
        )
        assert len(history) == 0


def test_history_ordering_by_timestamp(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Test translation"),
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
        s.flush()

        # Create history entries with different timestamps
        now = datetime.now(UTC)
        diff1 = compute_diff("Test translation", "diff1")
        diff2 = compute_diff("Test translation", "diff2")
        diff3 = compute_diff("Test translation", "diff3")
        history1 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff1,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.manual_edit,
            timestamp=now - timedelta(minutes=10),
        )
        history2 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff2,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.machine_translation,
            timestamp=now - timedelta(minutes=5),
        )
        history3 = DocumentRecordHistory(
            record_id=records[0].id,
            diff=diff3,
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.glossary_substitution,
            timestamp=now,
        )
        s.add_all([history1, history2, history3])
        s.commit()

        # Store IDs before session closes
        history1_id = history1.id
        history2_id = history2.id
        history3_id = history3.id

    response = user_logged_client.get("/document/records/1/history")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["history"]) == 3

    # Check ordering (newest first)
    assert response_data["history"][0]["id"] == history3_id
    assert response_data["history"][1]["id"] == history2_id
    assert response_data["history"][2]["id"] == history1_id


def test_merge_diffs_correctly_merges_consecutive_changes(
    user_logged_client: TestClient, session: Session
):
    """Test that multiple consecutive changes by the same author are properly merged."""
    with session as s:
        records = [
            DocumentRecord(
                source="Hello World", target="Test translation", approved=False
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

        # Create initial history entry with JSON diff format
        initial_diff = compute_diff("", "Test translation")
        initial_history = DocumentRecordHistory(
            record_id=records[0].id,
            diff=initial_diff,
            author_id=1,
            change_type=DocumentRecordHistoryChangeType.initial_import,
        )
        s.add(initial_history)
        s.commit()

    # First update: "Test translation" -> "Hello World"
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hello World",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Second update: "Hello World" -> "Hello World!" (same author, same type)
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hello World!",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that only one history entry exists (merged)
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .order_by(DocumentRecordHistory.timestamp.desc())
            .all()
        )
        assert len(history) == 2
        assert history[0].change_type == DocumentRecordHistoryChangeType.manual_edit
        assert history[0].diff

        # Verify that the merged diff correctly represents the full transformation
        # from "Test translation" to "Hello World!"
        diff_data = json.loads(history[0].diff)
        assert "ops" in diff_data
        assert "old_len" in diff_data

        # The old_len should be the length of the original text
        assert diff_data["old_len"] == len("Test translation")

        # Apply the diff to the original text should give us the final text
        result = apply_diff("Test translation", history[0].diff)
        assert result == "Hello World!"


def test_merge_diffs_with_insert_only_operations(
    user_logged_client: TestClient, session: Session
):
    """Test that merging works correctly when only insert operations are involved."""
    with session as s:
        records = [
            DocumentRecord(source="Hello", target="Hi", approved=False),
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

    # First update: "Hi" -> "Hi there"
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hi there",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Second update: "Hi there" -> "Hi there!" (same author, same type)
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hi there!",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that only one history entry exists (merged)
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .all()
        )
        assert len(history) == 1
        assert history[0].diff is not None

        # Verify the merged diff
        result = apply_diff("Hi", history[0].diff)
        assert result == "Hi there!"


def test_merge_diffs_with_multiple_history_records(
    user_logged_client: TestClient, session: Session
):
    """Test that multiple consecutive changes by the same author are properly merged."""
    with session as s:
        records = [
            DocumentRecord(source="Hello World", target="Replacement", approved=False),
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

        # Create initial history entry with JSON diff format
        first = DocumentRecordHistory(
            record_id=records[0].id,
            diff=compute_diff("", "Test translation"),
            author_id=None,
            change_type=DocumentRecordHistoryChangeType.initial_import,
        )
        second = DocumentRecordHistory(
            record_id=records[0].id,
            diff=compute_diff("Test translation", "Replacement"),
            author_id=2,
            change_type=DocumentRecordHistoryChangeType.machine_translation,
        )

        # add one by one to preserve timestamps
        s.add(first)
        s.commit()

        sleep(0.05)

        s.add(second)
        s.commit()

    # First update: "Replacement" -> "Hello World"
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hello World",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Second update: "Hello World" -> "Hello World!" (same author, same type)
    response = user_logged_client.put(
        "/document/records/1",
        json={
            "target": "Hello World!",
            "approved": False,
            "update_repetitions": False,
        },
    )
    assert response.status_code == 200

    # Check that only one history entry exists (merged)
    with session as s:
        history = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id == 1)
            .order_by(DocumentRecordHistory.timestamp.desc())
            .all()
        )
        assert len(history) == 3
        assert history[0].change_type == DocumentRecordHistoryChangeType.manual_edit
        assert history[0].diff

        # Verify that the merged diff correctly represents the full transformation
        # from "Replacement" to "Hello World!"
        diff_data = json.loads(history[0].diff)
        assert "ops" in diff_data
        assert "old_len" in diff_data

        # The old_len should be the length of the original text
        assert diff_data["old_len"] == len("Replacement")

        # Apply the diff to the original text should give us the final text
        result = apply_diff("Replacement", history[0].diff)
        assert result == "Hello World!"
