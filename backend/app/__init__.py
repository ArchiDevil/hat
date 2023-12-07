import os
from pathlib import Path
import sqlite3
from quart import (
    Quart,
    render_template,
    request,
    abort,
    send_file,
    current_app,
    redirect,
    url_for,
)

from app.tmx import extract_tmx_content
from app.xliff import extract_xliff_content
from app.db import get_session
from app.schema import TmxDocument, TmxRecord, XliffDocument, XliffRecord


def get_instance_path():
    instance_path = Path(current_app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True)
    return instance_path


def create_app(mode="Production"):
    app = Quart(__name__)
    app.config.from_object(f"app.settings.{mode}")
    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    app.config["DATABASE"] = db_url

    @app.route("/")
    async def index():
        with get_session() as session:
            tmx_files = session.query(TmxDocument).all()
            xliff_docs = session.query(XliffDocument).all()
        return await render_template(
            "index.html", tmx_files=tmx_files, xliff_docs=xliff_docs
        )

    @app.get("/tmx/<id_>")
    async def tmx(id_: int):
        with get_session() as session:
            tmx = session.query(TmxDocument).filter_by(id=id_).first()
            if not tmx:
                abort(404, f"TMX {id_} not found")
            return await render_template("tmx.html", tmx=tmx)

    @app.post("/tmx/upload")
    async def tmx_upload():
        files = await request.files
        tmx_data = files.get("tmx-file", None)
        if not tmx_data:
            abort(400, "Missing tmx file")
        tmx_data = tmx_data.read()
        tmx_data = extract_tmx_content(tmx_data)
        with get_session() as session:
            tmx = TmxDocument(name="test")
            session.add(tmx)
            session.commit()

            for source, target in tmx_data:
                tmx.records.append(TmxRecord(source=source, target=target))
            session.commit()

            new_id = tmx.id

        return redirect(url_for("tmx", id_=new_id))

    @app.post("/upload")
    async def upload():
        files = await request.files
        tmx_data = files.get("tmx-file", None)
        xliff_data = files.get("xliff-file", None)

        if not tmx_data or not xliff_data:
            abort(400, "Missing tmx or xliff file")

        tmx_data = tmx_data.read()
        xliff_data = xliff_data.read()

        # extract TMX pairs
        tmx_data = extract_tmx_content(tmx_data)

        # put them into an sqlite database
        db_path = get_instance_path() / "tmx.db"
        if not db_path.exists():
            db_path.touch()

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS tmx")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS tmx (
                source TEXT,
                target TEXT
            )
            """
        )
        c.executemany(
            """
            INSERT INTO tmx VALUES (?, ?)
            """,
            tmx_data,
        )
        conn.commit()

        # parse XLIFF file
        xliff_content = extract_xliff_content(xliff_data)

        # find original segments in a DB and put them into XLIFF
        originals = 0
        matches = 0
        for segment in xliff_content.segments:
            orig = segment.original
            originals += 1
            if not orig:
                continue

            c.execute(
                """
                SELECT target FROM tmx WHERE source = ? LIMIT 1
                """,
                (orig,),
            )
            result = c.fetchall()
            if not result:
                continue

            segment.translation = result[0][0]
            segment.approved = True
            matches += 1

        c.close()
        conn.close()

        xliff_content.commit()

        output_file = xliff_content.write()
        return await send_file(
            output_file,
            "application/xml",
            as_attachment=True,
            attachment_filename="output.xliff",
        )

    return app
