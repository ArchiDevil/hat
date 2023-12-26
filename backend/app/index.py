from pathlib import Path
from quart import Blueprint, current_app, render_template

from app.db import get_session
from app.schema import TmxDocument, XliffDocument


bp = Blueprint("app", __name__)


def get_instance_path():
    instance_path = Path(current_app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True)
    return instance_path


@bp.route("/")
async def index():
    with get_session() as session:
        tmx_files = session.query(TmxDocument).all()
        xliff_docs = session.query(XliffDocument).all()
    return await render_template(
        "index.html", tmx_files=tmx_files, xliff_docs=xliff_docs
    )
