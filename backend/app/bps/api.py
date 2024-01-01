from quart import Blueprint, abort, request
from sqlalchemy import select

from app.schema import TmxDocument, TmxRecord, XliffDocument, XliffRecord
from app.db import get_session
from app.tmx import extract_tmx_content
from app.xliff import extract_xliff_content

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
        return {"result": "ok"}


@bp.post("/tmx/upload")
async def tmx_upload():
    files = await request.files
    tmx_data = files.get("file", None)
    if not tmx_data:
        abort(400)

    filename = tmx_data.filename
    tmx_data = tmx_data.read()
    tmx_data = extract_tmx_content(tmx_data)
    with get_session() as session:
        doc = TmxDocument(name=filename)
        session.add(doc)
        session.commit()

        for source, target in tmx_data:
            doc.records.append(TmxRecord(source=source, target=target))
        session.commit()

    return {"result": "ok"}


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
        return {"result": "ok"}


@bp.post("/xliff/upload")
async def upload():
    files = await request.files
    xliff_data = files.get("file", None)
    if not xliff_data:
        abort(400)

    filename = xliff_data.filename
    xliff_data = xliff_data.read()
    original_document = xliff_data.decode("utf-8")
    xliff_data = extract_xliff_content(xliff_data)
    with get_session() as session:
        doc = XliffDocument(name=filename, original_document=original_document)
        session.add(doc)

        for segment in xliff_data.segments:
            if not segment.approved:
                tmx_data = session.execute(
                    select(TmxRecord.source, TmxRecord.target)
                    .where(TmxRecord.source == segment.original)
                    .limit(1)
                ).first()
                if tmx_data:
                    segment.translation = tmx_data.target
                    segment.approved = True

            doc.records.append(
                XliffRecord(
                    id=segment.id_, source=segment.original, target=segment.translation
                )
            )

        session.commit()

    return {"result": "ok"}
