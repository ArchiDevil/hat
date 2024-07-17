from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import models, schema
from app.db import get_db
from app.settings import settings


def get_current_user_id(
    session: Annotated[str | None, Cookie(include_in_schema=False)] = None,
) -> int:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
    data = serializer.loads(session)
    if "user_id" in data:
        return data["user_id"]

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


class RoleChecker:
    def __init__(self, role: models.UserRole) -> None:
        self.__role = role

    def __call__(
        self,
        user_id: Annotated[int, Depends(get_current_user_id)],
        db: Annotated[Session, Depends(get_db)],
    ):
        user = db.query(schema.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        if self.__role == models.UserRole.ADMIN and user.role == "admin":
            return

        if self.__role == models.UserRole.USER and user.role in ["user", "admin"]:
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


# TODO: do we need a moderator role in the future?
has_admin_role = RoleChecker(models.UserRole.ADMIN)
has_user_role = RoleChecker(models.UserRole.USER)
