from quart.testing import QuartClient

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
