from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session

from .settings import get_settings

engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def init_connection(connection_url: str):
    global engine, SessionLocal
    engine = create_engine(connection_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def close_connection():
    global engine
    if engine:
        engine.dispose()
        engine = None


def get_db():
    if not engine:
        init_connection(get_settings().database_url)

    assert SessionLocal
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
