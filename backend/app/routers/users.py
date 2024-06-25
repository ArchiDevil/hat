from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Cookie, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import schema, models
from app.db import get_db
from app.security import password_hasher
from app.settings import get_settings, Settings


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def get_users(db: Annotated[Session, Depends(get_db)]) -> list[models.User]:
    users = db.query(schema.User).order_by(schema.User.id).all()
    return [
        models.User(
            id=user.id,
            username=user.username,
            email=user.email,
            role=models.UserRole(user.role),
            disabled=user.disabled,
        )
        for user in users
    ]


@router.post("/")
def create_user(
    data: models.UserToCreate, db: Annotated[Session, Depends(get_db)]
) -> models.User:
    fields = data.model_dump()
    fields["role"] = fields["role"].value
    fields["password"] = password_hasher.hash(fields["password"])
    new_user = schema.User(**fields)
    db.add(new_user)
    db.commit()
    return models.User(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=models.UserRole(new_user.role),
        disabled=new_user.disabled,
    )


@router.post("/{user_id}")
def update_user(
    user_id: int, data: models.UserFields, db: Annotated[Session, Depends(get_db)]
) -> models.StatusMessage:
    user = db.query(schema.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = data.username
    user.email = data.email
    user.role = data.role.value
    user.disabled = data.disabled

    db.commit()

    return models.StatusMessage(message="ok")


def get_current_user_id(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[str | None, Cookie(include_in_schema=False)] = None,
) -> int:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
    data = serializer.loads(session)
    if "user_id" in data:
        return data["user_id"]

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/current")
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
