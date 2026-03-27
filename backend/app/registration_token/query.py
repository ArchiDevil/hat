import secrets
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.registration_token.models import RegistrationToken


class RegistrationTokenNotFoundExc(BaseQueryException):
    """Exception raised when registration token is not found."""


class RegistrationTokenQuery:
    """Contain queries for Registration Token operations."""

    def __init__(self, db: Session) -> None:
        self.__db = db

    def create(self, created_by: int) -> RegistrationToken:
        token = RegistrationToken(
            token=secrets.token_hex(16),  # 32 characters
            created_by=created_by,
        )
        self.__db.add(token)
        self.__db.commit()
        self.__db.refresh(token)
        return token

    def get_all(self) -> Sequence[RegistrationToken]:
        return (
            self.__db.execute(
                select(RegistrationToken).order_by(RegistrationToken.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_by_id(self, token_id: int) -> RegistrationToken | None:
        return self.__db.execute(
            select(RegistrationToken).where(RegistrationToken.id == token_id)
        ).scalar_one_or_none()

    def get_by_token(self, token: str) -> RegistrationToken | None:
        return self.__db.execute(
            select(RegistrationToken).where(RegistrationToken.token == token)
        ).scalar_one_or_none()

    def delete(self, token_id: int) -> None:
        token = self.get_by_id(token_id)
        if not token:
            raise RegistrationTokenNotFoundExc()

        self.__db.delete(token)
        self.__db.commit()
