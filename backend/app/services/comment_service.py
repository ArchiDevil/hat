"""Comment service for comment management operations."""

from sqlalchemy.orm import Session

from app.base.exceptions import EntityNotFound, UnauthorizedAccess
from app.comments.models import Comment
from app.comments.query import CommentsQuery
from app.comments.schema import CommentResponse, CommentUpdate
from app.models import StatusMessage


class CommentService:
    """Service for comment management operations."""

    def __init__(self, db: Session):
        self.__query = CommentsQuery(db)

    def get_comment(self, comment_id: int) -> Comment:
        """
        Get a comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment object

        Raises:
            EntityNotFound: If comment not found
        """
        comment = self.__query.get_comment(comment_id)
        if not comment:
            raise EntityNotFound("Comment not found")
        return comment

    def update_comment(
        self, comment_id: int, data: CommentUpdate, user_id: int, force: bool
    ) -> CommentResponse:
        """
        Update an existing comment.

        Args:
            comment_id: Comment ID
            data: Comment update data
            user_id: ID of user updating the comment
            force: Whether to force updating

        Returns:
            Updated CommentResponse object

        Raises:
            EntityNotFound: If comment not found
            UnauthorizedAccess: If user lacks permission
        """
        comment = self.get_comment(comment_id)
        self._check_authorship(comment, user_id, force)

        updated_comment = self.__query.update_comment(comment_id, data)
        return CommentResponse.model_validate(updated_comment)

    def delete_comment(
        self, comment_id: int, user_id: int, force: bool
    ) -> StatusMessage:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID
            user_id: ID of user deleting the comment
            force: Whether to force deletion

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If comment not found
            UnauthorizedAccess: If user lacks permission
        """
        comment = self.get_comment(comment_id)
        self._check_authorship(comment, user_id, force)

        self.__query.delete_comment(comment_id)
        return StatusMessage(message="Comment deleted successfully")

    def _check_authorship(self, comment: Comment, user_id: int, force: bool) -> None:
        """
        Check if user can modify/delete comment.

        Args:
            comment: Comment object
            user_id: ID of user attempting the action
            force: Whether to force the action

        Raises:
            UnauthorizedAccess: If user lacks permission
        """
        if not force and comment.created_by != user_id:
            raise UnauthorizedAccess("You can only modify your own comments")
