from quart.testing import QuartClient
from quart.datastructures import FileStorage


from app.db import get_session
from app.schema import XliffDocument, XliffRecord, TmxRecord, TmxDocument


async def test_can_show_xliff(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            records = [
                XliffRecord(source="test1", target="test1"),
                XliffRecord(source="test2", target="test2"),
            ]
            session.add(
                XliffDocument(name="test", records=records, original_document="")
            )
            session.commit()

    response = await client.get("/xliff/1")
    assert response.status_code == 200
    assert "test1" in (await response.data).decode("utf-8")
    assert "test2" in (await response.data).decode("utf-8")


async def test_shows_404_for_unknown_xliff(client: QuartClient):
    response = await client.get("/xliff/1")
    assert response.status_code == 404


async def test_download_xliff(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            tmx_records = [
                TmxRecord(source="Regional Effects", target="RegEffectsTranslation")
            ]
            session.add(TmxDocument(name="test", records=tmx_records))
            session.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = await client.post(
            "/xliff/upload", files={"xliff-file": FileStorage(stream=fp)}
        )

    response = await client.get("/xliff/1/download")
    assert response.status_code == 200

    data = (await response.data).decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "RegEffectsTranslation" in data


async def test_download_shows_404_for_unknown_xliff(client: QuartClient):
    response = await client.get("/xliff/1/download")
    assert response.status_code == 404
