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


@router.get("/")
def get_users(db: Annotated[Session, Depends(get_db)]) -> list[models.User]:
    service = UserService(db)
    return service.get_users()


@router.post("/")
def create_user(
    data: models.UserToCreate, db: Annotated[Session, Depends(get_db)]
) -> models.User:
    service = UserService(db)
    return service.create_user(data)


@router.post("/{user_id}")
def update_user(
    user_id: int, data: models.UserFields, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    service = UserService(db)
    try:
        return service.update_user(user_id, data)
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
