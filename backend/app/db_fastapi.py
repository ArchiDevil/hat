from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session

from .settings_fastapi import get_settings

engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def init_connection(connection_url: str):
    eng = create_engine(connection_url)
    maker = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return eng, maker


def get_db():
    global engine, SessionLocal
    if not engine:
        engine, SessionLocal = init_connection(get_settings().database_url)

    assert SessionLocal
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
