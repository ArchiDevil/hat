from quart.testing import QuartClient
from quart.datastructures import FileStorage

from app.db import get_session
from app.schema import TmxDocument, TmxRecord, XliffDocument, XliffRecord


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


async def test_can_get_xliff_file(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            xliff_records = [
                XliffRecord(source="Regional Effects", target="Translation"),
                XliffRecord(source="User Interface", target="UI"),
            ]
            session.add(
                XliffDocument(
                    name="test_doc.xliff",
                    original_document="Something",
                    records=xliff_records,
                )
            )
            session.commit()

    response = await client.get("/api/xliff/1")
    assert response.status_code == 200
    assert await response.json == {
        "id": 1,
        "name": "test_doc.xliff",
        "records": [
            {
                "id": 1,
                "source": "Regional Effects",
                "target": "Translation",
            },
            {
                "id": 2,
                "source": "User Interface",
                "target": "UI",
            },
        ],
    }


async def test_returns_404_when_xliff_file_not_found(client: QuartClient):
    response = await client.get("/api/xliff/1")
    assert response.status_code == 404


async def test_can_delete_xliff_doc(client: QuartClient):
    async with client.app.app_context():
        with get_session() as session:
            session.add(XliffDocument(name="first_doc.tmx", original_document=""))
            session.commit()

    response = await client.post("/api/xliff/1/delete")
    assert response.status_code == 200
    assert await response.data == b'{"result":"ok"}\n'

    async with client.app.app_context():
        with get_session() as session:
            assert session.query(XliffDocument).count() == 0


async def test_returns_404_when_deleting_nonexistent_xliff_doc(client: QuartClient):
    response = await client.post("/api/xliff/1/delete")
    assert response.status_code == 404


async def test_upload(client: QuartClient):
    with open("tests/small.xliff", "rb") as fp:
        response = await client.post(
            "/api/xliff/upload", files={"file": FileStorage(stream=fp)}
        )
    assert response.status_code == 200

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
            "/api/xliff/upload", files={"file": FileStorage(stream=fp)}
        )
    assert response.status_code == 200

    async with client.app.app_context():
        with get_session() as session:
            doc = session.query(XliffDocument).filter_by(id=1).first()
            assert doc is not None
            assert doc.records[0].target == "Translation"


async def test_upload_no_file(client: QuartClient):
    response = await client.post("/api/xliff/upload", files={})
    assert response.status_code == 400
