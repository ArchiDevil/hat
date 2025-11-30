from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.comments.models import Comment
from app.comments.schema import CommentCreate, CommentUpdate


class CommentNotFoundExc(BaseQueryException):
    """Exception raised when comment is not found"""


class CommentsQuery:
    """Contain queries for Comment operations"""

    def __init__(self, db: Session) -> None:
        self.__db = db

    def create_comment(
        self, comment_data: CommentCreate, author_id: int, document_record_id: int
    ) -> Comment:
        """Create a new comment"""
        comment = Comment(
            text=comment_data.text,
            author_id=author_id,
            document_record_id=document_record_id,
            updated_at=datetime.now(UTC),
        )
        self.__db.add(comment)
        self.__db.commit()
        self.__db.refresh(comment)
        return comment

    def get_comment(self, comment_id: int) -> Comment | None:
        """Get a comment by ID"""
        return self.__db.execute(
            select(Comment).filter(Comment.id == comment_id)
        ).scalar_one_or_none()

    def get_comments_by_document_record(
        self, document_record_id: int
    ) -> Sequence[Comment]:
        """Get all comments for a document record"""
        return (
            self.__db.execute(
                select(Comment)
                .filter(Comment.document_record_id == document_record_id)
                .order_by(Comment.updated_at)
            )
            .scalars()
            .all()
        )

    def update_comment(self, comment_id: int, comment_data: CommentUpdate) -> Comment:
        """Update an existing comment"""
        comment = self.get_comment(comment_id)
        if not comment:
            raise CommentNotFoundExc()

        comment.text = comment_data.text
        comment.updated_at = datetime.now(UTC)
        self.__db.commit()
        self.__db.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> None:
        """Delete a comment"""
        comment = self.get_comment(comment_id)
        if not comment:
            raise CommentNotFoundExc()

        self.__db.delete(comment)
        self.__db.commit()
