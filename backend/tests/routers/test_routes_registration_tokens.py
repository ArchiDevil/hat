from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.registration_token.models import RegistrationToken


class TestCreateToken:
    """Tests for POST /registration_tokens/ endpoint."""

    def test_admin_can_create_token(self, admin_logged_client: TestClient):
        response = admin_logged_client.post("/registration_tokens/")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "token" in data
        assert len(data["token"]) == 32  # 16 bytes hex-encoded = 32 chars
        assert "created_at" in data
        assert data["created_by"] == 2  # admin user id

    def test_user_cannot_create_token(self, user_logged_client: TestClient):
        response = user_logged_client.post("/registration_tokens/")
        assert response.status_code == 403

    def test_non_logged_cannot_create_token(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.post("/registration_tokens/")
        assert response.status_code == 401


class TestListTokens:
    """Tests for GET /registration_tokens/ endpoint."""

    def test_admin_can_list_tokens(
        self, admin_logged_client: TestClient, session: Session
    ):
        # Create some tokens first
        with session as s:
            s.add(
                RegistrationToken(
                    token="a" * 32,
                    created_by=2,
                )
            )
            s.add(
                RegistrationToken(
                    token="b" * 32,
                    created_by=2,
                )
            )
            s.commit()

        response = admin_logged_client.get("/registration_tokens/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_tokens_empty(self, admin_logged_client: TestClient):
        response = admin_logged_client.get("/registration_tokens/")
        assert response.status_code == 200
        assert response.json() == []

    def test_user_cannot_list_tokens(
        self, user_logged_client: TestClient, session: Session
    ):
        response = user_logged_client.get("/registration_tokens/")
        assert response.status_code == 403

    def test_non_logged_cannot_list_tokens(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.get("/registration_tokens/")
        assert response.status_code == 401


class TestDeleteToken:
    """Tests for DELETE /registration_tokens/{token_id} endpoint."""

    def test_admin_can_delete_token(
        self, admin_logged_client: TestClient, session: Session
    ):
        # Create a token first
        with session as s:
            token = RegistrationToken(
                token="c" * 32,
                created_by=2,
            )
            s.add(token)
            s.commit()
            token_id = token.id

        response = admin_logged_client.delete(f"/registration_tokens/{token_id}")

        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

        # Verify token is deleted
        response = admin_logged_client.get("/registration_tokens/")
        assert len(response.json()) == 0

    def test_delete_nonexistent_token_returns_404(
        self, admin_logged_client: TestClient, session: Session
    ):
        response = admin_logged_client.delete("/registration_tokens/999")
        assert response.status_code == 404

    def test_user_cannot_delete_token(
        self, user_logged_client: TestClient, session: Session
    ):
        # Create a token first
        with session as s:
            s.add(
                RegistrationToken(
                    token="d" * 32,
                    created_by=2,
                )
            )
            s.commit()

        response = user_logged_client.delete("/registration_tokens/1")

        assert response.status_code == 403

    def test_non_logged_cannot_delete_token(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.delete("/registration_tokens/1")
        assert response.status_code == 401
