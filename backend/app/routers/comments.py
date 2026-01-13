from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schema
from app.base.exceptions import EntityNotFound, UnauthorizedAccess
from app.comments.schema import CommentResponse, CommentUpdate
from app.db import get_db
from app.models import StatusMessage
from app.services import CommentService
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/comments", tags=["comments"], dependencies=[Depends(has_user_role)]
)


@router.put("/{comment_id}")
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> CommentResponse:
    """Update an existing comment"""
    service = CommentService(db)
    user = db.query(schema.User).filter_by(id=current_user).one()
    try:
        return service.update_comment(
            comment_id, comment_data, current_user, force=user.role == "admin"
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedAccess as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> StatusMessage:
    """Delete a comment"""
    service = CommentService(db)
    user = db.query(schema.User).filter_by(id=current_user).one()
    try:
        return service.delete_comment(
            comment_id, current_user, force=user.role == "admin"
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedAccess as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
