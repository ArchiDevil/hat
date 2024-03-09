import os
import tempfile

from fastapi.testclient import TestClient
import pytest

from app import create_app, db, schema
from app.db import init_connection


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
