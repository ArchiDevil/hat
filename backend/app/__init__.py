import os
from quart import Quart

from app import index
from app.bps import tmx, xliff, api


def create_app(mode="Production", additional_config=None):
    app = Quart(__name__)

    app.config.from_object(f"app.settings.{mode}")
    app.config.update(additional_config or {})

    if app.config.get("DATABASE") is None:
        db_url = os.environ.get(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        app.config["DATABASE"] = db_url

    app.register_blueprint(index.bp)
    app.register_blueprint(tmx.bp)
    app.register_blueprint(xliff.bp)
    app.register_blueprint(api.bp)

    return app
