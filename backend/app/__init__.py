from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, tmx, xliff, users


def create_app():
    app = FastAPI()

    # TODO: it would be nice to make it debug-only
    origins = [
        "http://localhost:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(tmx.router)
    app.include_router(xliff.router)
    app.include_router(users.router)

    return app
