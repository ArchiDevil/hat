from quart.testing import QuartClient

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
