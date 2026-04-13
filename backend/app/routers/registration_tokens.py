"""Router for Registration Token endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import StatusMessage
from app.permissions import P, PermissionChecker
from app.registration_token.schema import RegistrationTokenResponse
from app.services.registration_token_service import RegistrationTokenService
from app.user.depends import get_current_user_id

router = APIRouter(
    prefix="/registration_tokens",
    tags=["tokens"],
    dependencies=[Depends(PermissionChecker(P.USER_MANAGE))],
)


def get_service(db: Annotated[Session, Depends(get_db)]) -> RegistrationTokenService:
    return RegistrationTokenService(db)


@router.post("/")
def create_token(
    current_user: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[RegistrationTokenService, Depends(get_service)],
) -> RegistrationTokenResponse:
    return service.create_token(current_user)


@router.get("/")
def list_tokens(
    service: Annotated[RegistrationTokenService, Depends(get_service)],
) -> list[RegistrationTokenResponse]:
    return service.list_tokens()


@router.delete("/{token_id}")
def delete_token(
    token_id: int,
    service: Annotated[RegistrationTokenService, Depends(get_service)],
) -> StatusMessage:
    try:
        return service.delete_token(token_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
