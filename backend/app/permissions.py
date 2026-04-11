from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schema import User
from app.user.depends import get_current_user_id


class P:
    GLOSSARY_READ = "glossary:read"
    GLOSSARY_UPLOAD = "glossary:upload"
    GLOSSARY_DOWNLOAD = "glossary:download"
    GLOSSARY_CREATE = "glossary:create"
    GLOSSARY_UPDATE = "glossary:update"
    GLOSSARY_DELETE = "glossary:delete"
    GLOSSARY_RECORD_CREATE = "glossary_record:create"


ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset(
        {
            P.GLOSSARY_READ,
            P.GLOSSARY_CREATE,
            P.GLOSSARY_UPDATE,
            P.GLOSSARY_DELETE,
            P.GLOSSARY_RECORD_CREATE,
            P.GLOSSARY_UPLOAD,
            P.GLOSSARY_DOWNLOAD,
        }
    ),
    "user": frozenset(
        {
            P.GLOSSARY_READ,
            P.GLOSSARY_RECORD_CREATE,
        }
    ),
}


class PermissionChecker:
    def __init__(self, permission: str) -> None:
        self._permission = permission

    def __call__(
        self,
        user_id: Annotated[int, Depends(get_current_user_id)],
        db: Annotated[Session, Depends(get_db)],
    ):
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        role_perms = ROLE_PERMISSIONS.get(user.role, frozenset())
        if self._permission not in role_perms:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
