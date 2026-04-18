from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    api_tokens,
    auth,
    comments,
    document,
    glossary,
    projects,
    records,
    registration_tokens,
    translation_memory,
    user,
    users,
)
from app.settings import settings

ROUTERS = (
    api_tokens,
    auth,
    comments,
    document,
    records,
    translation_memory,
    user,
    users,
    glossary,
    projects,
    registration_tokens,
)


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
