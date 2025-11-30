from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schema
from app.comments.query import CommentsQuery
from app.comments.schema import CommentResponse, CommentUpdate
from app.db import get_db
from app.models import StatusMessage
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/comments", tags=["comments"], dependencies=[Depends(has_user_role)]
)


def get_comment_by_id(db: Session, comment_id: int):
    """Helper function to get comment by ID"""
    comment = CommentsQuery(db).get_comment(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    return comment


def check_comment_authorship(comment, current_user_id: int, is_admin: bool = False):
    """Check if user can modify/delete comment"""
    if not is_admin and comment.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own comments",
        )


@router.put("/{comment_id}")
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> CommentResponse:
    """Update an existing comment"""
    comment = get_comment_by_id(db, comment_id)

    # Check if user can modify this comment
    user = db.query(schema.User).filter_by(id=current_user).one()
    is_admin = user.role == "admin"
    check_comment_authorship(comment, current_user, is_admin)

    updated_comment = CommentsQuery(db).update_comment(comment_id, comment_data)
    return CommentResponse.model_validate(updated_comment)


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[int, Depends(get_current_user_id)],
) -> StatusMessage:
    """Delete a comment"""
    comment = get_comment_by_id(db, comment_id)

    # Check if user can delete this comment
    user = db.query(schema.User).filter_by(id=current_user).one()
    is_admin = user.role == "admin"
    check_comment_authorship(comment, current_user, is_admin)

    CommentsQuery(db).delete_comment(comment_id)
    return StatusMessage(message="Comment deleted successfully")
