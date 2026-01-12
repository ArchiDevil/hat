"""User service for user management operations."""

from sqlalchemy.orm import Session

from app import models, schema
from app.base.exceptions import EntityNotFound
from app.security import hash_password


class UserService:
    """Service for user management operations."""

    def __init__(self, db: Session):
        self.__db = db

    def get_current_user(self, user_id: int) -> models.User:
        """
        Get current user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            EntityNotFound: If user not found
        """
        user = self.__db.query(schema.User).filter_by(id=user_id).first()
        if not user:
            raise EntityNotFound("User", user_id)

        return models.User(
            id=user.id,
            username=user.username,
            email=user.email,
            role=models.UserRole(user.role),
            disabled=user.disabled,
        )

    def get_users(self) -> list[models.User]:
        """
        Get all users.

        Returns:
            List of User objects
        """
        users = self.__db.query(schema.User).order_by(schema.User.id).all()
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

    def create_user(self, data: models.UserToCreate) -> models.User:
        """
        Create a new user.

        Args:
            data: User creation data

        Returns:
            Created User object
        """
        fields = data.model_dump()
        fields["role"] = fields["role"].value
        fields["password"] = hash_password(fields["password"])
        new_user = schema.User(**fields)
        self.__db.add(new_user)
        self.__db.commit()
        return models.User(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            role=models.UserRole(new_user.role),
            disabled=new_user.disabled,
        )

    def update_user(
        self, user_id: int, data: models.UserFields
    ) -> models.StatusMessage:
        """
        Update an existing user.

        Args:
            user_id: User ID to update
            data: User fields to update

        Returns:
            StatusMessage indicating success

        Raises:
            EntityNotFound: If user not found
        """
        user = self.__db.query(schema.User).filter_by(id=user_id).first()
        if not user:
            raise EntityNotFound("User", user_id)

        user.username = data.username
        user.email = data.email
        user.role = data.role.value
        user.disabled = data.disabled

        self.__db.commit()

        return models.StatusMessage(message="ok")
