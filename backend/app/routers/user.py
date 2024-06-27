from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schema
from app.auth import get_current_user_id
from app.db import get_db

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/")
def get_current_user(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
) -> models.User:
    user = db.query(schema.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return models.User(
        id=user.id,
        username=user.username,
        email=user.email,
        role=models.UserRole(user.role),
        disabled=user.disabled,
    )
