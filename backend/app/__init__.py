import os


def create_app(mode="Production", additional_config=None):
    from quart import Quart
    from quart_cors import cors
    from app.bps import api_tmx, api_xliff

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


def create_fastapi_app():
    from fastapi import FastAPI
    from app.routers import tmx

    app = FastAPI()
    app.include_router(tmx.router)

    return app
