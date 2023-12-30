from quart import Blueprint, render_template, abort
from app.db import get_session
from app.schema import TmxDocument


bp = Blueprint("tmx", __name__, url_prefix="/tmx")


@bp.get("/<id_>")
async def index(id_: int):
    with get_session() as session:
        doc = session.query(TmxDocument).filter_by(id=id_).first()
        if not doc:
            abort(404)
        return await render_template("tmx.html", tmx=doc)
