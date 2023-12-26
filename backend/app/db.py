from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from quart import current_app, g

from app import schema


def init_connection():
    engine = create_engine(current_app.config["DATABASE"])
    g.engine = engine
    session_factory = sessionmaker(bind=engine)
    g.sessionmaker = scoped_session(session_factory)


def close_connection():
    g.pop("sessionmaker", None)
    engine: Engine | None = g.pop("engine", None)
    if engine is not None:
        engine.dispose()


def reinit_schema():
    init_connection()
    schema.Base.metadata.drop_all(g.engine)
    schema.Base.metadata.create_all(g.engine)
    close_connection()


@contextmanager
def get_session():
    if "engine" not in g:
        init_connection()
    try:
        session: Session = g.sessionmaker()
        yield session
    finally:
        session.close()
