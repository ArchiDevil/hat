from quart import Blueprint, redirect, render_template, abort, request, url_for

from app.db import get_session
from app.schema import TmxDocument, TmxRecord
from app.tmx import extract_tmx_content


bp = Blueprint("tmx", __name__, url_prefix="/tmx")


@bp.get("/<id_>")
async def index(id_: int):
    with get_session() as session:
        doc = session.query(TmxDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)
        return await render_template("tmx.html", tmx=doc)


@bp.post("/upload")
async def tmx_upload():
    files = await request.files
    tmx_data = files.get("tmx-file", None)
    if not tmx_data:
        abort(400)
    tmx_data = tmx_data.read()
    tmx_data = extract_tmx_content(tmx_data)
    with get_session() as session:
        doc = TmxDocument(name="test")
        session.add(doc)
        session.commit()

        for source, target in tmx_data:
            doc.records.append(TmxRecord(source=source, target=target))
        session.commit()

        new_id = doc.id

    return redirect(url_for("tmx.index", id_=new_id))


@bp.get("/<id_>/delete")
async def tmx_delete(id_: int):
    with get_session() as session:
        doc = session.query(TmxDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)
        session.delete(doc)
        session.commit()
    return redirect(url_for("app.index"))
