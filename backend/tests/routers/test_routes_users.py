from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.permissions import ROLE_PERMISSIONS

# pylint: disable=C0116


def test_can_get_current_user(user_logged_client: TestClient, session: Session):
    response = user_logged_client.get("/user/")
    assert response.status_code == 200
    data = response.json()
    assert data.pop("permissions") == sorted(ROLE_PERMISSIONS["user"])
    assert data == {
        "id": 1,
        "username": "test",
        "email": "test@test.com",
        "role": models.UserRole.USER.value,
        "disabled": False,
    }


def test_cannot_get_current_user_for_non_logged_in(
    fastapi_client: TestClient, session: Session
):
    response = fastapi_client.get("/user/")
    assert response.status_code == 401
