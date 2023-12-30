from quart.testing import QuartClient
from quart.datastructures import FileStorage

from app.db import get_session
from app.schema import TmxDocument, TmxRecord


async def test_can_show_tmx(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            records = [
                TmxRecord(source="test1", target="test1"),
                TmxRecord(source="test2", target="test2"),
            ]
            session.add(TmxDocument(name="test", records=records))
            session.commit()

    response = await client.get("/tmx/1")
    assert response.status_code == 200
    assert "test1" in (await response.data).decode("utf-8")
    assert "test2" in (await response.data).decode("utf-8")


async def test_shows_404_if_tmx_not_found(client: QuartClient):
    response = await client.get("/tmx/1")
    assert response.status_code == 404


async def test_can_upload_tmx(client: QuartClient):
    with open("tests/small.tmx", "rb") as f:
        response = await client.post(
            "/tmx/upload",
            files={"tmx-file": FileStorage(stream=f)},
        )
    assert response.status_code == 302
    assert "tmx/1" in response.location

    async with client.app.app_context():
        with get_session() as session:
            doc = session.query(TmxDocument).filter_by(id=1).first()
            assert doc is not None
            assert doc.name == "tests/small.tmx"
            assert len(doc.records) == 1
            assert "Handbook" in doc.records[0].source


async def test_shows_404_when_no_file_uploaded(client: QuartClient):
    response = await client.post("/tmx/upload")
    assert response.status_code == 400
