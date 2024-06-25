from datetime import datetime, timedelta, UTC
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import schema, models
from app.db import get_db
from app.settings import get_settings, Settings
from app.security import password_hasher
from app.routers.users import get_current_user_id


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    data: models.AuthFields,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    response: Response,
) -> models.StatusMessage:
    if not data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(schema.User).filter_by(email=data.email).first()

    if not user or not password_hasher.verify(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
    # TODO: would be nice to have "permanent" option for the session
    # TODO: check that it works properly with a domain name
    response.set_cookie(
        "session",
        serializer.dumps({"user_id": user.id}),
        secure=bool(settings.domain_name),
        domain=settings.domain_name,
        httponly=True,
        expires=datetime.now(UTC) + timedelta(days=14),
    )
    return models.StatusMessage(message="Logged in")


@router.post("/logout", dependencies=[Depends(get_current_user_id)])
def logout(response: Response) -> models.StatusMessage:
    response.delete_cookie("session")
    return models.StatusMessage(message="Logged out")
