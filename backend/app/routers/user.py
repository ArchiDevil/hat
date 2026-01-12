from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.base.exceptions import EntityNotFound
from app.db import get_db
from app.services import UserService
from app.user.depends import get_current_user_id

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/")
def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    service = UserService(db)
    try:
        return service.get_current_user(user_id)
    except EntityNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))
