from typing import Annotated

from fastapi import Cookie, HTTPException, status
from itsdangerous import URLSafeTimedSerializer

from app.settings import settings


def get_current_user_id(
    session: Annotated[str | None, Cookie(include_in_schema=False)] = None,
) -> int:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
    data = serializer.loads(session)
    if "user_id" in data:
        return data["user_id"]

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
