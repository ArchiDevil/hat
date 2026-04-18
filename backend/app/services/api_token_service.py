import hashlib
import secrets

from sqlalchemy.orm import Session

from app.api_token.query import ApiTokenQuery
from app.api_token.schema import (
    ApiTokenCreatedResponse,
    ApiTokenCreateRequest,
    ApiTokenResponse,
)
from app.base.exceptions import EntityNotFound
from app.models import StatusMessage


class ApiTokenService:
    def __init__(self, db: Session) -> None:
        self.__query = ApiTokenQuery(db)

    def create_token(
        self, data: ApiTokenCreateRequest, created_by: int
    ) -> ApiTokenCreatedResponse:
        raw_token = f"hat_{secrets.token_hex(32)}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = self.__query.create(
            name=data.name,
            token_hash=token_hash,
            user_id=data.user_id,
            created_by=created_by,
            expires_at=data.expires_at,
        )
        return ApiTokenCreatedResponse(
            id=token.id,
            name=token.name,
            user_id=token.user_id,
            created_by=token.created_by,
            created_at=token.created_at,
            expires_at=token.expires_at,
            last_used_at=token.last_used_at,
            token=raw_token,
        )

    def list_tokens(self) -> list[ApiTokenResponse]:
        tokens = self.__query.get_all()
        return [ApiTokenResponse.model_validate(t) for t in tokens]

    def delete_token(self, token_id: int) -> StatusMessage:
        try:
            self.__query.delete(token_id)
        except Exception:
            raise EntityNotFound("Api Token", token_id)
        return StatusMessage(message="ok")
