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

    TM_READ = "tm:read"
    TM_CREATE = "tm:create"
    TM_DELETE = "tm:delete"
    TM_UPLOAD = "tm:upload"
    TM_DOWNLOAD = "tm:download"

    RECORD_READ = "record:read"
    RECORD_EDIT = "record:edit"

    DOCUMENT_READ = "document:read"
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DOWNLOAD = "document:download"
    DOCUMENT_PROCESS = "document:process"

    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_RESOURCES = "project:manage_resources"

    COMMENT_CREATE = "comment:create"
    COMMENT_MANAGE = "comment:manage"

    USER_MANAGE = "user:manage"


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
            P.TM_READ,
            P.TM_CREATE,
            P.TM_DELETE,
            P.TM_UPLOAD,
            P.TM_DOWNLOAD,
            P.RECORD_READ,
            P.RECORD_EDIT,
            P.DOCUMENT_READ,
            P.DOCUMENT_CREATE,
            P.DOCUMENT_DELETE,
            P.DOCUMENT_UPDATE,
            P.DOCUMENT_DOWNLOAD,
            P.DOCUMENT_PROCESS,
            P.PROJECT_READ,
            P.PROJECT_CREATE,
            P.PROJECT_UPDATE,
            P.PROJECT_DELETE,
            P.PROJECT_MANAGE_RESOURCES,
            P.COMMENT_CREATE,
            P.COMMENT_MANAGE,
            P.USER_MANAGE,
        }
    ),
    "user": frozenset(
        {
            P.GLOSSARY_READ,
            P.GLOSSARY_RECORD_CREATE,
            P.TM_READ,
            P.RECORD_READ,
            P.RECORD_EDIT,
            P.DOCUMENT_READ,
            P.PROJECT_READ,
            P.COMMENT_CREATE,
            P.COMMENT_MANAGE,
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
