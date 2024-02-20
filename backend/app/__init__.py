import os
from quart import Quart
from quart_cors import cors

from app.bps import api_tmx, api_xliff


def create_app(mode="Production", additional_config=None):
    app = Quart(__name__)

    if app.debug:
        app = cors(app, allow_origin="*")

    app.config.from_object(f"app.settings.{mode}")
    app.config.update(additional_config or {})

    if app.config.get("DATABASE") is None:
        db_url = os.environ.get(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        app.config["DATABASE"] = db_url

    app.register_blueprint(
        cors(api_tmx.bp, allow_origin="*") if app.debug else api_tmx.bp
    )
    app.register_blueprint(
        cors(api_xliff.bp, allow_origin="*") if app.debug else api_xliff.bp
    )

    return app
