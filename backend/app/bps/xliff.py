from quart import Blueprint, redirect, render_template, abort, request, url_for
from sqlalchemy import select

from app.db import get_session
from app.schema import TmxRecord, XliffDocument, XliffRecord
from app.xliff import extract_xliff_content


bp = Blueprint("xliff", __name__, url_prefix="/xliff")


@bp.get("/<id_>")
async def index(id_: int):
    with get_session() as session:
        doc = session.query(XliffDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)
        return await render_template("xliff.html", xliff=doc)


@bp.post("/upload")
async def upload():
    files = await request.files
    xliff_data = files.get("xliff-file", None)
    if not xliff_data:
        abort(400)

    xliff_data = xliff_data.read()
    xliff_data = extract_xliff_content(xliff_data)
    with get_session() as session:
        doc = XliffDocument(name="test")
        session.add(doc)
        session.commit()

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
                XliffRecord(source=segment.original, target=segment.translation)
            )

        session.commit()
        new_id = doc.id

    return redirect(url_for("xliff.index", id_=new_id))


@bp.get("/<id_>/delete")
async def delete(id_: int):
    with get_session() as session:
        doc = session.query(XliffDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)

        session.delete(doc)
        session.commit()

    return redirect(url_for("app.index"))
