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


async def test_upload(client: QuartClient):
    with open("tests/small.xliff", "rb") as fp:
        response = await client.post(
            "/xliff/upload", files={"xliff-file": FileStorage(stream=fp)}
        )
    assert response.status_code == 302
    assert "xliff/1" in response.location

    async with client.app.app_context():
        with get_session() as session:
            doc = session.query(XliffDocument).filter_by(id=1).first()
            assert doc is not None
            assert doc.name == "tests/small.xliff"
            assert len(doc.records) == 1
            assert doc.records[0].id == 675606
            assert doc.records[0].document_id == 1
            assert doc.original_document.startswith("<?xml version=")


async def test_upload_process_xliff_file(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            tmx_records = [TmxRecord(source="Regional Effects", target="Translation")]
            session.add(TmxDocument(name="test", records=tmx_records))
            session.commit()

    with open("tests/small.xliff", "rb") as fp:
        response = await client.post(
            "/xliff/upload", files={"xliff-file": FileStorage(stream=fp)}
        )
    assert response.status_code == 302
    assert "xliff/1" in response.location

    async with client.app.app_context():
        with get_session() as session:
            doc = session.query(XliffDocument).filter_by(id=1).first()
            assert doc is not None
            assert doc.records[0].target == "Translation"


async def test_upload_no_file(client: QuartClient):
    response = await client.post("/xliff/upload", files={})
    assert response.status_code == 400


async def test_delete(client: QuartClient):
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

    response = await client.get("/xliff/1/delete")
    assert response.status_code == 302

    async with client.app.app_context():
        with get_session() as session:
            assert session.query(XliffDocument).filter_by(id=1).first() is None


async def test_delete_not_found(client: QuartClient):
    response = await client.get("/xliff/1/delete")
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
