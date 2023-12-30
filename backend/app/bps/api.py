from quart import Blueprint, abort

from app.schema import TmxDocument, XliffDocument
from app.db import get_session

bp = Blueprint("api", __name__, url_prefix="/api")

# TMX things


@bp.get("/tmx")
async def tmx_files():
    with get_session() as session:
        docs = session.query(TmxDocument).all()
        return [
            {
                "id": doc.id,
                "name": doc.name,
            }
            for doc in docs
        ]


@bp.post("/tmx/<int:doc_id>/delete")
async def delete_tmx(doc_id: int):
    with get_session() as session:
        doc = session.query(TmxDocument).filter(TmxDocument.id == doc_id).first()
        if not doc:
            abort(404)

        session.delete(doc)
        session.commit()
        return "ok"


# XLIFF things


@bp.get("/xliff")
async def xliff_files():
    with get_session() as session:
        docs = session.query(XliffDocument).all()
        return [
            {
                "id": doc.id,
                "name": doc.name,
            }
            for doc in docs
        ]


@bp.post("/xliff/<int:doc_id>/delete")
async def delete_xliff(doc_id: int):
    with get_session() as session:
        doc = session.query(XliffDocument).filter(XliffDocument.id == doc_id).first()
        if not doc:
            abort(404)

        session.delete(doc)
        session.commit()
        return "ok"
