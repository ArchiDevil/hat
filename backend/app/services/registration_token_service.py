"""Service layer for Registration Token operations."""

from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound
from app.models import StatusMessage
from app.registration_token.query import RegistrationTokenQuery
from app.registration_token.schema import RegistrationTokenResponse


class RegistrationTokenService:
    """Service for registration token operations."""

    def __init__(self, db: Session) -> None:
        self.__query = RegistrationTokenQuery(db)

    def create_token(self, created_by: int) -> RegistrationTokenResponse:
        token = self.__query.create(created_by)
        return RegistrationTokenResponse.model_validate(token)

    def list_tokens(self) -> list[RegistrationTokenResponse]:
        tokens = self.__query.get_all()
        return [RegistrationTokenResponse.model_validate(t) for t in tokens]

    def delete_token(self, token_id: int) -> StatusMessage:
        try:
            self.__query.delete(token_id)
        except Exception:
            raise EntityNotFound("Registration Token", token_id)

        return StatusMessage(message="ok")
