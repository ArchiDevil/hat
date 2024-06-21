from contextlib import contextmanager

from fastapi.testclient import TestClient
import pytest

from app import schema, models
from app.db import get_db


@contextmanager
def session():
    return get_db()


def test_can_log_in(fastapi_client: TestClient):
    with session() as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.commit()

    response = fastapi_client.post(
        "/auth/login", json={"email": "test@test.com", "password": "1234"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged in"}
    assert response.cookies["session"] is not None


@pytest.mark.parametrize("password", ["1234", ""])
def test_returns_403_for_invalid_password(
    fastapi_client: TestClient, password: str | None
):
    with session() as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyXM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.commit()

    response = fastapi_client.post(
        "/auth/login", json={"email": "test@test.com", "password": password}
    )
    assert response.status_code == 401


def test_returns_403_for_disabled(fastapi_client: TestClient):
    with session() as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.add(
            schema.User(
                username="another test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="some_test@test.com",
                role=models.UserRole.USER.value,
                disabled=True,
            )
        )
        s.commit()

    response = fastapi_client.post(
        "/auth/login", json={"email": "some_test@test.com", "password": "1234"}
    )
    assert response.status_code == 403


def test_can_logout(fastapi_client: TestClient):
    with session() as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.commit()

    fastapi_client.post(
        "/auth/login", json={"email": "test@test.com", "password": "1234"}
    )

    response = fastapi_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    assert not response.cookies


def test_logout_rejects_non_logged(fastapi_client: TestClient):
    response = fastapi_client.post("/auth/logout")
    assert response.status_code == 401
