import hashlib
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.api_token.query import ApiTokenQuery
from app.db import get_db
from app.settings import settings


def get_current_user_id(
    db: Annotated[Session, Depends(get_db)],
    session: Annotated[str | None, Cookie(include_in_schema=False)] = None,
    authorization: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> int:
    if session:
        serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
        data = serializer.loads(session)
        if "user_id" in data:
            return data["user_id"]

    if authorization and authorization.startswith("Bearer "):
        query = ApiTokenQuery(db)
        raw_token = authorization[7:]
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        api_token = query.get_by_hash(token_hash)
        if api_token:
            if api_token.expires_at:
                exp = api_token.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=UTC)
                if exp < datetime.now(UTC):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            query.update_last_used(api_token.id)
            return api_token.user_id

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
