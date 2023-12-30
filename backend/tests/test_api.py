from quart.testing import QuartClient
from quart.datastructures import FileStorage

from app.db import get_session
from app.schema import TmxDocument, XliffDocument


async def test_can_return_list_of_tmx_docs(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            session.add(TmxDocument(name="first_doc.tmx"))
            session.add(TmxDocument(name="another_doc.tmx"))
            session.commit()

    response = await client.get("/api/tmx")
    assert response.status_code == 200
    assert await response.json == [
        {
            "id": 1,
            "name": "first_doc.tmx",
        },
        {
            "id": 2,
            "name": "another_doc.tmx",
        },
    ]


async def test_can_delete_tmx_doc(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            session.add(TmxDocument(name="first_doc.tmx"))
            session.commit()

    response = await client.post("/api/tmx/1/delete")
    assert response.status_code == 200
    assert await response.data == b"ok"

    async with client.app.app_context():
        with get_session() as session:
            assert session.query(TmxDocument).count() == 0


async def test_returns_404_when_deleting_nonexistent_tmx_doc(client: QuartClient):
    response = await client.post("/api/tmx/1/delete")
    assert response.status_code == 404


async def test_can_upload_tmx(client: QuartClient):
    with open("tests/small.tmx", "rb") as f:
        response = await client.post(
            "/api/tmx/upload",
            files={"file": FileStorage(stream=f)},
        )
    assert response.status_code == 200

    async with client.app.app_context():
        with get_session() as session:
            doc = session.query(TmxDocument).filter_by(id=1).first()
            assert doc is not None
            assert doc.name == "tests/small.tmx"
            assert len(doc.records) == 1
            assert "Handbook" in doc.records[0].source


async def test_shows_404_when_no_file_uploaded(client: QuartClient):
    response = await client.post("/api/tmx/upload")
    assert response.status_code == 400


async def test_can_get_list_of_xliff_docs(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            session.add(XliffDocument(name="first_doc.tmx", original_document=""))
            session.add(XliffDocument(name="another_doc.tmx", original_document=""))
            session.commit()

    response = await client.get("/api/xliff")
    assert response.status_code == 200
    assert await response.json == [
        {
            "id": 1,
            "name": "first_doc.tmx",
        },
        {
            "id": 2,
            "name": "another_doc.tmx",
        },
    ]


async def test_can_delete_xliff_doc(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            session.add(XliffDocument(name="first_doc.tmx", original_document=""))
            session.commit()

    response = await client.post("/api/xliff/1/delete")
    assert response.status_code == 200
    assert await response.data == b"ok"

    async with client.app.app_context():
        with get_session() as session:
            assert session.query(XliffDocument).count() == 0


async def test_returns_404_when_deleting_nonexistent_xliff_doc(client: QuartClient):
    response = await client.post("/api/xliff/1/delete")
    assert response.status_code == 404
