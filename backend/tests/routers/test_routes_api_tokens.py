import hashlib

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_token.models import ApiToken


class TestCreateApiToken:
    def test_admin_can_create_token(self, admin_logged_client: TestClient):
        response = admin_logged_client.post(
            "/api_tokens/",
            json={"name": "test-token", "user_id": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "test-token"
        assert data["user_id"] == 1
        assert data["created_by"] == 2
        assert "token" in data
        assert data["token"].startswith("hat_")
        assert len(data["token"]) == 68
        assert "token_hash" not in data

    def test_user_cannot_create_token(self, user_logged_client: TestClient):
        response = user_logged_client.post(
            "/api_tokens/",
            json={"name": "test-token", "user_id": 1},
        )
        assert response.status_code == 403

    def test_non_logged_cannot_create_token(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.post(
            "/api_tokens/",
            json={"name": "test-token", "user_id": 1},
        )
        assert response.status_code == 401


class TestListApiTokens:
    def test_admin_can_list_tokens(
        self, admin_logged_client: TestClient, session: Session
    ):
        with session as s:
            s.add(
                ApiToken(
                    name="token-a",
                    token_hash="hash_a",
                    user_id=1,
                    created_by=2,
                )
            )
            s.add(
                ApiToken(
                    name="token-b",
                    token_hash="hash_b",
                    user_id=1,
                    created_by=2,
                )
            )
            s.commit()

        response = admin_logged_client.get("/api_tokens/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_tokens_empty(self, admin_logged_client: TestClient):
        response = admin_logged_client.get("/api_tokens/")
        assert response.status_code == 200
        assert response.json() == []

    def test_user_cannot_list_tokens(self, user_logged_client: TestClient):
        response = user_logged_client.get("/api_tokens/")
        assert response.status_code == 403

    def test_non_logged_cannot_list_tokens(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.get("/api_tokens/")
        assert response.status_code == 401


class TestDeleteApiToken:
    def test_admin_can_delete_token(
        self, admin_logged_client: TestClient, session: Session
    ):
        with session as s:
            token = ApiToken(
                name="to-delete",
                token_hash="hash_c",
                user_id=1,
                created_by=2,
            )
            s.add(token)
            s.commit()
            token_id = token.id

        response = admin_logged_client.delete(f"/api_tokens/{token_id}")

        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

        response = admin_logged_client.get("/api_tokens/")
        assert len(response.json()) == 0

    def test_delete_nonexistent_token_returns_404(
        self, admin_logged_client: TestClient
    ):
        response = admin_logged_client.delete("/api_tokens/999")
        assert response.status_code == 404

    def test_user_cannot_delete_token(
        self, user_logged_client: TestClient, session: Session
    ):
        with session as s:
            s.add(
                ApiToken(
                    name="user-token",
                    token_hash="hash_d",
                    user_id=1,
                    created_by=2,
                )
            )
            s.commit()

        response = user_logged_client.delete("/api_tokens/1")
        assert response.status_code == 403

    def test_non_logged_cannot_delete_token(
        self, fastapi_client: TestClient, session: Session
    ):
        response = fastapi_client.delete("/api_tokens/1")
        assert response.status_code == 401


class TestCreateApiTokenResponse:
    def test_raw_token_returned_not_stored(
        self, admin_logged_client: TestClient, session: Session
    ):
        response = admin_logged_client.post(
            "/api_tokens/",
            json={"name": "verify-token", "user_id": 1},
        )

        assert response.status_code == 200
        data = response.json()
        raw_token = data["token"]
        assert raw_token.startswith("hat_")

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        with session as s:
            db_token = s.query(ApiToken).filter_by(id=data["id"]).first()
            assert db_token
            assert db_token.token_hash == token_hash
            assert db_token.token_hash != raw_token
