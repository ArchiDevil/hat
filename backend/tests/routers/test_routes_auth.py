import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, schema
from app.registration_token.models import RegistrationToken


def test_can_log_in(fastapi_client: TestClient, session: Session):
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
        s.commit()

    response = fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": "1234", "remember": False},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged in"}
    assert response.cookies["session"]


def test_can_log_in_with_remember(fastapi_client: TestClient, session: Session):
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
        s.commit()

    response = fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": "1234", "remember": True},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged in"}
    assert response.cookies["session"]


@pytest.mark.parametrize("password", ["1234", ""])
def test_returns_403_for_invalid_password(
    fastapi_client: TestClient, password: str | None, session: Session
):
    with session as s:
        s.add(
            schema.User(
                username="test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyXM",
                email="test@test.com",
                role=models.UserRole.USER.value,
                disabled=False,
            )
        )
        s.commit()

    response = fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": password, "remember": False},
    )
    assert response.status_code == 401


def test_returns_403_for_disabled(fastapi_client: TestClient, session: Session):
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
                username="another test",
                password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
                email="some_test@test.com",
                role=models.UserRole.USER.value,
                disabled=True,
            )
        )
        s.commit()

    response = fastapi_client.post(
        "/auth/login",
        json={"email": "some_test@test.com", "password": "1234", "remember": False},
    )
    assert response.status_code == 403


def test_can_logout(fastapi_client: TestClient, session: Session):
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
        s.commit()

    fastapi_client.post(
        "/auth/login",
        json={"email": "test@test.com", "password": "1234", "remember": False},
    )

    response = fastapi_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    assert not response.cookies


def test_logout_rejects_non_logged(fastapi_client: TestClient):
    response = fastapi_client.post("/auth/logout")
    assert response.status_code == 401


# Signup tests


def test_can_signup_with_valid_token(fastapi_client: TestClient, session: Session):
    # Create an admin user first to create the registration token
    with session as s:
        admin = schema.User(
            username="admin",
            password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
            email="admin@test.com",
            role=models.UserRole.ADMIN.value,
            disabled=False,
        )
        s.add(admin)
        s.commit()
        s.refresh(admin)

        token = RegistrationToken(
            token="test-registration-token-123", created_by=admin.id
        )
        s.add(token)
        s.commit()

    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "securepassword123",
            "registration_token": "test-registration-token-123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["username"] == "newuser"
    assert data["role"] == "user"
    assert data["disabled"] is False
    assert "id" in data


def test_signup_deletes_token_after_use(fastapi_client: TestClient, session: Session):
    # Create an admin user and registration token
    with session as s:
        admin = schema.User(
            username="admin",
            password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
            email="admin@test.com",
            role=models.UserRole.ADMIN.value,
            disabled=False,
        )
        s.add(admin)
        s.commit()
        s.refresh(admin)

        token = RegistrationToken(token="single-use-token", created_by=admin.id)
        s.add(token)
        s.commit()

    # First signup should succeed
    response1 = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "user1@test.com",
            "username": "user1",
            "password": "password123",
            "registration_token": "single-use-token",
        },
    )
    assert response1.status_code == 200

    # Second signup with same token should fail
    response2 = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "user2@test.com",
            "username": "user2",
            "password": "password123",
            "registration_token": "single-use-token",
        },
    )
    assert response2.status_code == 403
    assert "Incorrect token provided" in response2.json()["detail"]


def test_signup_returns_403_for_invalid_token(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "securepassword123",
            "registration_token": "invalid-token",
        },
    )

    assert response.status_code == 403
    assert "Incorrect token provided" in response.json()["detail"]


def test_signup_returns_422_for_missing_email(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "username": "newuser",
            "password": "securepassword123",
            "registration_token": "some-token",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_missing_username(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "newuser@test.com",
            "password": "securepassword123",
            "registration_token": "some-token",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_missing_password(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "newuser@test.com",
            "username": "newuser",
            "registration_token": "some-token",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_missing_registration_token(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 422


def test_signup_returns_422_for_invalid_email_format(fastapi_client: TestClient):
    response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "not-an-email",
            "username": "newuser",
            "password": "securepassword123",
            "registration_token": "some-token",
        },
    )

    assert response.status_code == 422


def test_signup_new_user_can_login_after_registration(
    fastapi_client: TestClient, session: Session
):
    # Create an admin user and registration token
    with session as s:
        admin = schema.User(
            username="admin",
            password="$pbkdf2-sha256$29000$R4gxRkjpnXNOqXXundP6Xw$pzr2kyXZjurvt6sUv7NF4dQhpHdv9RBtlGbOStnFyUM",
            email="admin@test.com",
            role=models.UserRole.ADMIN.value,
            disabled=False,
        )
        s.add(admin)
        s.commit()
        s.refresh(admin)

        token = RegistrationToken(token="login-test-token", created_by=admin.id)
        s.add(token)
        s.commit()

    # Sign up
    signup_response = fastapi_client.post(
        "/auth/signup",
        json={
            "email": "loginuser@test.com",
            "username": "loginuser",
            "password": "mypassword123",
            "registration_token": "login-test-token",
        },
    )
    assert signup_response.status_code == 200

    # Try to login with the same credentials
    login_response = fastapi_client.post(
        "/auth/login",
        json={
            "email": "loginuser@test.com",
            "password": "mypassword123",
            "remember": False,
        },
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"message": "Logged in"}
    assert login_response.cookies["session"]
