import os
import tempfile
import pytest
from quart import Quart

from app import create_app
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
