from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api_token.models import ApiToken
from app.base.exceptions import BaseQueryException


class ApiTokenNotFoundExc(BaseQueryException):
    pass


class ApiTokenQuery:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def create(
        self,
        name: str,
        token_hash: str,
        user_id: int,
        created_by: int,
        expires_at: datetime | None = None,
    ) -> ApiToken:
        token = ApiToken(
            name=name,
            token_hash=token_hash,
            user_id=user_id,
            created_by=created_by,
            expires_at=expires_at,
        )
        self.__db.add(token)
        self.__db.commit()
        self.__db.refresh(token)
        return token

    def get_by_hash(self, token_hash: str) -> ApiToken | None:
        return self.__db.execute(
            select(ApiToken).where(ApiToken.token_hash == token_hash)
        ).scalar_one_or_none()

    def get_all(self) -> Sequence[ApiToken]:
        return (
            self.__db.execute(select(ApiToken).order_by(ApiToken.created_at.desc()))
            .scalars()
            .all()
        )

    def get_by_id(self, token_id: int) -> ApiToken | None:
        return self.__db.execute(
            select(ApiToken).where(ApiToken.id == token_id)
        ).scalar_one_or_none()

    def delete(self, token_id: int) -> None:
        token = self.get_by_id(token_id)
        if not token:
            raise ApiTokenNotFoundExc()
        self.__db.delete(token)
        self.__db.commit()

    def update_last_used(self, token_id: int) -> None:
        self.__db.execute(
            update(ApiToken)
            .where(ApiToken.id == token_id)
            .values(last_used_at=datetime.now(UTC))
        )
        self.__db.commit()
