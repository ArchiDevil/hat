from pathlib import Path
import sqlite3
from quart import Quart, render_template, request, abort

from tmx import extract_tmx_content
from xliff import extract_xliff_content


def create_app(mode="Production"):
    app = Quart(__name__)
    app.config.from_object(f"settings.{mode}")

    if not Path(app.instance_path).exists():
        Path(app.instance_path).mkdir(parents=True)

    @app.route("/")
    async def index():
        return await render_template("index.html")

    @app.post("/upload")
    async def upload():
        tmx_data = (await request.files).get("tmx-file")
        xliff_data = (await request.files).get("xliff-file")

        if not tmx_data or not xliff_data:
            abort(400, "Missing tmx or xliff file")

        tmx_data = [
            line.decode(encoding="utf-8").strip() for line in tmx_data.readlines()
        ]
        xliff_data = [
            line.decode(encoding="utf-8").strip() for line in xliff_data.readlines()
        ]

        # extract TMX pairs
        tmx_data = extract_tmx_content(" ".join(tmx_data))

        # put them into an sqlite database
        db_path = Path(app.instance_path) / "tmx.db"
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
        xliff_content = extract_xliff_content(" ".join(xliff_data))

        # find original segments in a DB and put them into XLIFF
        originals = 0
        matches = 0
        for segment in xliff_content.segments():
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
            matches += 1

        c.close()
        conn.close()

        # provide new XLIFF content

        return await render_template(
            "upload.html",
            tmx_data=tmx_data,
            xliff_data=xliff_content,
            originals=originals if originals else 1,
            matches=matches,
        )

    return app


if __name__ == "__main__":
    create_app("Development").run(debug=True)
