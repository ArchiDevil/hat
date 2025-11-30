from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    comments,
    document,
    glossary,
    translation_memory,
    user,
    users,
)
from app.settings import settings

ROUTERS = (auth, comments, document, translation_memory, user, users, glossary)


def create_app():
    fastapi = FastAPI()

    fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_routers(fastapi)
    return fastapi


def register_routers(fastapi: FastAPI):
    for router in ROUTERS:
        fastapi.include_router(router.router)


app = create_app()
