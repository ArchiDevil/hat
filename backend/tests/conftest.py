import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models, schema
from app.db import Base, get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture()
def fastapi_client():
    yield client


@pytest.fixture()
def user_logged_client(fastapi_client: TestClient, session: Session):
    with session as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.add(
            schema.User(
                username="test-admin",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="admin@test.com",
                role=models.UserRole.ADMIN.value,
                disabled=False,
            )
        )
        s.commit()

    fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": "1234", "remember": False},
    )

    yield fastapi_client
