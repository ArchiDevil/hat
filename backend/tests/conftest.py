from contextlib import contextmanager
import os
import tempfile

from fastapi.testclient import TestClient
import pytest

from app import create_app, db, schema, models
from app.db import init_connection, get_db

# pylint: disable=C0116


@contextmanager
def session():
    return get_db()


@pytest.fixture()
def fastapi_app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app()
    init_connection(f"sqlite:///{db_path}")
    assert db.engine and db.SessionLocal

    schema.Base.metadata.drop_all(db.engine)
    schema.Base.metadata.create_all(db.engine)

    yield app

    db.close_connection()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def fastapi_client(fastapi_app):
    yield TestClient(fastapi_app)


@pytest.fixture()
def user_logged_client(fastapi_client: TestClient):
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
                username="test-admin",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="admin@test.com",
                role=models.UserRole.ADMIN.value,
                disabled=False,
            )
        )
        s.commit()

    fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": "1234", "remember": False},
    )

    yield fastapi_client
