from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import EntityNotFound
from app.db import get_db
from app.services import UserService
from app.user.depends import has_admin_role

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(has_admin_role)]
)


def get_service(db: Annotated[Session, Depends(get_db)]):
    return UserService(db)


@router.get("/")
def get_users(
    service: Annotated[UserService, Depends(get_service)],
) -> list[models.User]:
    return service.get_users()


@router.post("/")
def create_user(
    data: models.UserToCreate, service: Annotated[UserService, Depends(get_service)]
) -> models.User:
    return service.create_user(data)


@router.post("/{user_id}")
def update_user(
    user_id: int,
    data: models.UserFields,
    service: Annotated[UserService, Depends(get_service)],
) -> models.StatusMessage:
    try:
        return service.update_user(user_id, data)
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
