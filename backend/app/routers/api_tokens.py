from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api_token.schema import (
    ApiTokenCreatedResponse,
    ApiTokenCreateRequest,
    ApiTokenResponse,
)
from app.db import get_db
from app.models import StatusMessage
from app.permissions import P, PermissionChecker
from app.services.api_token_service import ApiTokenService
from app.user.depends import get_current_user_id

router = APIRouter(
    prefix="/api_tokens",
    tags=["apitokens"],
    dependencies=[Depends(PermissionChecker(P.USER_MANAGE))],
)


def get_service(db: Annotated[Session, Depends(get_db)]) -> ApiTokenService:
    return ApiTokenService(db)


@router.post("/")
def create_token(
    data: ApiTokenCreateRequest,
    current_user: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[ApiTokenService, Depends(get_service)],
) -> ApiTokenCreatedResponse:
    return service.create_token(data, current_user)


@router.get("/")
def list_tokens(
    service: Annotated[ApiTokenService, Depends(get_service)],
) -> list[ApiTokenResponse]:
    return service.list_tokens()


@router.delete("/{token_id}")
def delete_token(
    token_id: int,
    service: Annotated[ApiTokenService, Depends(get_service)],
) -> StatusMessage:
    try:
        return service.delete_token(token_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
