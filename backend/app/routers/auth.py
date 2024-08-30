from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import models, schema
from app.db import get_db
from app.security import verify_password
from app.settings import settings
from app.user.depends import has_user_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    data: models.AuthFields,
    response: Response,
    db: Session = Depends(get_db),
) -> models.StatusMessage:
    if not data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(schema.User).filter_by(email=data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

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


@router.post("/logout", dependencies=[Depends(has_user_role)])
def logout(response: Response) -> models.StatusMessage:
    response.delete_cookie("session")
    return models.StatusMessage(message="Logged out")
