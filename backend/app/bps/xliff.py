from quart import (
    Blueprint,
    redirect,
    render_template,
    abort,
    request,
    send_file,
    url_for,
)
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
        new_id = doc.id

    return redirect(url_for("xliff.index", id_=new_id))


@bp.get("/<id_>/download")
async def download(id_: int):
    # TODO: this is an extremely slow solution, but it works for now, fine for PoC
    with get_session() as session:
        doc = session.query(XliffDocument).filter_by(id=id_).first()

        if not doc:
            abort(404)

        original_document = doc.original_document.encode("utf-8")
        processed_document = extract_xliff_content(original_document)

        for segment in processed_document.segments:
            record = session.query(TmxRecord).filter_by(source=segment.original).first()
            if record:
                segment.translation = record.target

        processed_document.commit()
        file = processed_document.write()

    return await send_file(file, mimetype="application/xliff+xml")
