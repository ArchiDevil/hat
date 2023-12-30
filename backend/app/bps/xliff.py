from quart import (
    Blueprint,
    render_template,
    abort,
    send_file,
)

from app.db import get_session
from app.schema import TmxRecord, XliffDocument
from app.xliff import extract_xliff_content


bp = Blueprint("xliff", __name__, url_prefix="/xliff")


@bp.get("/<id_>")
async def index(id_: int):
    with get_session() as session:
        doc = session.query(XliffDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)
        return await render_template("xliff.html", xliff=doc)


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
