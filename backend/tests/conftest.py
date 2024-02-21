import os
import tempfile
from quart import Quart

from fastapi.testclient import TestClient
import pytest

from app import create_app, create_fastapi_app, db_fastapi, schema
from app.db_fastapi import init_connection
from app.db import reinit_schema, close_connection


@pytest.fixture()
async def app():
    db_fd, db_path = tempfile.mkstemp()

    application = create_app(
        mode="Testing", additional_config={"DATABASE": f"sqlite:///{db_path}"}
    )
    application.teardown_appcontext(lambda e: close_connection())

    async with application.app_context():
        reinit_schema()

    yield application

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
async def client(app: Quart):
    return app.test_client()


# FAST API THINGS


@pytest.fixture()
def fastapi_app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_fastapi_app()
    init_connection(f"sqlite:///{db_path}")
    assert db_fastapi.engine and db_fastapi.SessionLocal

    schema.Base.metadata.drop_all(db_fastapi.engine)
    schema.Base.metadata.create_all(db_fastapi.engine)

    yield app

    db_fastapi.close_connection()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def fastapi_client(fastapi_app):
    yield TestClient(fastapi_app)
