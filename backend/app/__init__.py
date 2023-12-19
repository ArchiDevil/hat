import os
from quart import Quart

from app import index
from app import tmx_bp


def create_app(mode="Production"):
    app = Quart(__name__)
    app.config.from_object(f"app.settings.{mode}")
    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    app.config["DATABASE"] = db_url
    app.register_blueprint(index.bp)
    app.register_blueprint(tmx_bp.bp)

    return app
