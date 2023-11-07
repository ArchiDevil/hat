from quart import Quart, render_template, request, abort

from tmx import extract_tmx_content


def create_app(mode="Production"):
    app = Quart(__name__)
    app.config.from_object(f"settings.{mode}")

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

        pairs = extract_tmx_content("".join(tmx_data))

        return await render_template(
            "upload.html",
            tmx_data=pairs,
            xliff_data=xliff_data,
        )

    return app


if __name__ == "__main__":
    app = create_app("Development")
    app.run(debug=True)
