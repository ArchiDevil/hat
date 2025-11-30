import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.comments.models import Comment
from app.documents.models import Document, DocumentRecord, DocumentType
from app.models import UserRole

# pylint: disable=C0116


def test_can_get_comments_for_record(user_logged_client: TestClient, session: Session):
    """Test getting all comments for a document record"""
    with session as s:
        # Create document with records
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
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

        # Add comments for the first record
        comments = [
            Comment(
                text="First comment",
                author_id=1,
                document_record_id=1,
                updated_at=datetime.datetime.now(datetime.UTC),
            ),
            Comment(
                text="Second comment",
                author_id=1,
                document_record_id=1,
                updated_at=datetime.datetime.now(datetime.UTC),
            ),
        ]
        for comment in comments:
            s.add(comment)
        s.commit()

    response = user_logged_client.get("/document/1/comments")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["text"] == "First comment"
    assert response_data[0]["author_id"] == 1
    assert response_data[0]["document_record_id"] == 1
    assert response_data[1]["text"] == "Second comment"


def test_get_comments_returns_empty_for_no_comments(
    user_logged_client: TestClient, session: Session
):
    """Test getting comments for record with no comments"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/comments")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == []


def test_get_comments_returns_404_for_nonexistent_record(
    user_logged_client: TestClient,
):
    """Test getting comments for nonexistent record"""
    response = user_logged_client.get("/document/999/comments")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document record not found"


def test_can_create_comment(user_logged_client: TestClient, session: Session):
    """Test creating a new comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.commit()

    comment_data = {"text": "This is a test comment"}
    response = user_logged_client.post("/document/1/comments", json=comment_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["text"] == "This is a test comment"
    assert response_data["author_id"] == 1
    assert response_data["document_record_id"] == 1
    assert "id" in response_data
    assert "updated_at" in response_data


def test_create_comment_returns_404_for_nonexistent_record(
    user_logged_client: TestClient,
):
    """Test creating comment for nonexistent record"""
    comment_data = {"text": "This is a test comment"}
    response = user_logged_client.post("/document/999/comments", json=comment_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Document record not found"


def test_create_comment_requires_text(user_logged_client: TestClient, session: Session):
    """Test that creating comment requires text field"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.post("/document/1/comments", json={})
    assert response.status_code == 422  # Validation error


def test_create_comment_requires_min_length_text(
    user_logged_client: TestClient, session: Session
):
    """Test that creating comment requires minimum length text"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.post("/document/1/comments", json={"text": ""})
    assert response.status_code == 422  # Validation error


def test_create_comment_requires_authentication(
    fastapi_client: TestClient, session: Session
):
    """Test that creating comment requires authentication"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )
        s.commit()

    comment_data = {"text": "This is a test comment"}
    response = fastapi_client.post("/document/1/comments", json=comment_data)
    assert response.status_code == 401  # Unauthorized


def test_can_update_own_comment(user_logged_client: TestClient, session: Session):
    """Test that user can update their own comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        comment = Comment(
            text="Original text",
            author_id=1,  # Same user as logged in
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    update_data = {"text": "Updated text"}
    response = user_logged_client.put(f"/comments/{comment_id}", json=update_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["text"] == "Updated text"
    assert response_data["id"] == comment_id


def test_cannot_update_others_comment(user_logged_client: TestClient, session: Session):
    """Test that user cannot update another user's comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        # Create comment by different user (id=2)
        from app import schema

        other_user = (
            s.query(schema.User).filter(schema.User.username == "test-admin").one()
        )
        comment = Comment(
            text="Original text",
            author_id=other_user.id,  # Different user
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    update_data = {"text": "Updated text"}
    response = user_logged_client.put(f"/comments/{comment_id}", json=update_data)
    assert response.status_code == 403  # Forbidden
    assert response.json()["detail"] == "You can only modify your own comments"


def test_can_delete_own_comment(user_logged_client: TestClient, session: Session):
    """Test that user can delete their own comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        comment = Comment(
            text="Original text",
            author_id=1,  # Same user as logged in
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    response = user_logged_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Comment deleted successfully"

    # Verify comment is deleted
    with session as s:
        deleted_comment = s.query(Comment).filter(Comment.id == comment_id).first()
        assert deleted_comment is None


def test_cannot_delete_others_comment(user_logged_client: TestClient, session: Session):
    """Test that user cannot delete another user's comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        # Create comment by different user (id=2)
        from app import schema

        other_user = (
            s.query(schema.User).filter(schema.User.username == "test-admin").one()
        )
        comment = Comment(
            text="Original text",
            author_id=other_user.id,  # Different user
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    response = user_logged_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 403  # Forbidden
    assert response.json()["detail"] == "You can only modify your own comments"

    # Verify comment still exists
    with session as s:
        existing_comment = s.query(Comment).filter(Comment.id == comment_id).first()
        assert existing_comment is not None


def test_update_comment_returns_404_for_nonexistent_comment(
    user_logged_client: TestClient,
):
    """Test updating nonexistent comment"""
    update_data = {"text": "Updated text"}
    response = user_logged_client.put("/comments/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_delete_comment_returns_404_for_nonexistent_comment(
    user_logged_client: TestClient,
):
    """Test deleting nonexistent comment"""
    response = user_logged_client.delete("/comments/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_comment_endpoints_require_authentication(fastapi_client: TestClient):
    """Test that comment endpoints require authentication"""
    # Clear any existing cookies to ensure clean state
    fastapi_client.cookies.clear()

    # Test GET comments
    response = fastapi_client.get("/document/1/comments")
    assert response.status_code == 401

    # Test POST comment
    response = fastapi_client.post("/document/1/comments", json={"text": "test"})
    assert response.status_code == 401

    # Test PUT comment
    response = fastapi_client.put("/comments/1", json={"text": "test"})
    assert response.status_code == 401

    # Test DELETE comment
    response = fastapi_client.delete("/comments/1")
    assert response.status_code == 401


def test_admin_can_update_any_comment(
    admin_logged_client: TestClient, session: Session
):
    """Test that admin can update any comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        # Create comment by regular user (id=1)
        comment = Comment(
            text="Original text",
            author_id=1,  # Regular user
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    update_data = {"text": "Admin updated text"}
    response = admin_logged_client.put(f"/comments/{comment_id}", json=update_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["text"] == "Admin updated text"


def test_admin_can_delete_any_comment(
    admin_logged_client: TestClient, session: Session
):
    """Test that admin can delete any comment"""
    with session as s:
        records = [DocumentRecord(source="Hello World", target="Привет Мир")]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
            )
        )

        # Create comment by regular user (id=1)
        comment = Comment(
            text="Original text",
            author_id=1,  # Regular user
            document_record_id=1,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        s.add(comment)
        s.commit()
        comment_id = comment.id

    response = admin_logged_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Comment deleted successfully"

    # Verify comment is deleted
    with session as s:
        deleted_comment = s.query(Comment).filter(Comment.id == comment_id).first()
        assert deleted_comment is None


@pytest.fixture()
def admin_logged_client(fastapi_client: TestClient, session: Session):
    """Create a client logged in as admin user"""
    from app import schema

    with session as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="test@test.com",
                role=UserRole.USER.value,
                disabled=False,
            )
        )
        s.add(
            schema.User(
                username="test-admin",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="admin@test.com",
                role=UserRole.ADMIN.value,
                disabled=False,
            )
        )
        s.commit()

    fastapi_client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "1234", "remember": False},
    )

    yield fastapi_client
