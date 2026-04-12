from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import BusinessLogicError, UnauthorizedAccess
from app.db import get_db
from app.services import AuthService
from app.services.user_service import UserService
from app.settings import settings
from app.user.depends import get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db: Annotated[Session, Depends(get_db)]):
    return AuthService(db)


def get_user_service(db: Annotated[Session, Depends(get_db)]):
    return UserService(db)


@router.post("/login")
def login(
    data: models.AuthFields,
    response: Response,
    service: Annotated[AuthService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        user = service.login(data)
        # Set session cookie in router (HTTP-specific concern)
        serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
        response.set_cookie(
            "session",
            serializer.dumps({"user_id": user.id}),
            secure=bool(settings.domain_name),
            domain=settings.domain_name,
            httponly=True,
            expires=datetime.now(UTC) + timedelta(days=21) if data.remember else None,
        )
        return models.StatusMessage(message="Logged in")
    except UnauthorizedAccess as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/logout", dependencies=[Depends(get_current_user_id)])
def logout(response: Response) -> models.StatusMessage:
    # Logout doesn't need database access, just clear the cookie
    response.delete_cookie("session")
    return models.StatusMessage(message="Logged out")


@router.post("/signup")
def signup(
    data: models.SignupFields,
    service: Annotated[UserService, Depends(get_user_service)],
) -> models.User:
    try:
        return service.create_user(
            models.UserToCreate(
                email=data.email,
                username=data.username,
                role=models.UserRole.USER,
                disabled=False,
                password=data.password,
            ),
            registration_token=data.registration_token,
        )
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
