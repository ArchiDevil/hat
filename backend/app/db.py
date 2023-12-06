from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from quart import current_app, g


@contextmanager
def get_session() -> Generator[scoped_session, None, None]:
    # this is the first request to the DB
    if "engine" not in g:
        init_connection()
    try:
        session = g.sessionmaker()
        yield session
    finally:
        g.sessionmaker.remove()


def init_connection():
    engine = create_engine(current_app.config["DATABASE"])
    g.engine = engine
    session_factory = sessionmaker(bind=engine)
    g.sessionmaker = scoped_session(session_factory)


def close_connection(e=None):
    g.pop("sessionmaker", None)
    engine = g.pop("engine", None)
    if engine is not None:
        engine.dispose()
