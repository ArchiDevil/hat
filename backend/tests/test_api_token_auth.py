import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api_token.models import ApiToken
from app.schema import User


def _seed_users(session: Session):
    with session as s:
        s.add(
            User(
                username="test",
                password="x",
                email="test@test.com",
                role="user",
                disabled=False,
            )
        )
        s.add(
            User(
                username="test-admin",
                password="x",
                email="admin@test.com",
                role="admin",
                disabled=False,
            )
        )
        s.commit()


def _create_token_in_db(session: Session, **overrides) -> str:
    raw_token = f"hat_{'ab' * 32}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    defaults = dict(
        name="test",
        token_hash=token_hash,
        user_id=2,
        created_by=2,
    )
    defaults.update(overrides)
    with session as s:
        token = ApiToken(**defaults)
        s.add(token)
        s.commit()
    return raw_token


class TestBearerTokenAuth:
    def test_bearer_token_authenticates(
        self, fastapi_client: TestClient, session: Session
    ):
        fastapi_client.cookies.clear()
        _seed_users(session)
        raw_token = _create_token_in_db(session, user_id=2)

        response = fastapi_client.get(
            "/api_tokens/",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

        assert response.status_code == 200

    def test_expired_token_rejected(self, fastapi_client: TestClient, session: Session):
        fastapi_client.cookies.clear()
        _seed_users(session)
        raw_token = _create_token_in_db(
            session,
            user_id=2,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        response = fastapi_client.get(
            "/api_tokens/",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

        assert response.status_code == 401

    def test_invalid_token_rejected(self, fastapi_client: TestClient, session: Session):
        fastapi_client.cookies.clear()
        response = fastapi_client.get(
            "/api_tokens/",
            headers={"Authorization": "Bearer hat_invalid_token"},
        )

        assert response.status_code == 401

    def test_cookie_auth_still_works(self, user_logged_client: TestClient):
        response = user_logged_client.get("/user/")
        assert response.status_code == 200

    def test_cookie_takes_precedence_over_bearer(
        self, admin_logged_client: TestClient, session: Session
    ):
        raw_token = _create_token_in_db(session, user_id=1)

        response = admin_logged_client.get(
            "/user/",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

        data = response.json()
        assert response.status_code == 200
        assert data["email"] == "admin@test.com"

    def test_last_used_at_updated(self, fastapi_client: TestClient, session: Session):
        fastapi_client.cookies.clear()
        _seed_users(session)
        raw_token = _create_token_in_db(session, user_id=2)

        response = fastapi_client.get(
            "/api_tokens/",
            headers={"Authorization": f"Bearer {raw_token}"},
        )

        assert response.status_code == 200

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        with session as s:
            result = s.execute(
                select(ApiToken).where(ApiToken.token_hash == token_hash)
            ).scalar_one()
            assert result.last_used_at is not None
