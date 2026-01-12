"""Authentication service for user login/logout operations."""

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import models, schema
from app.base.exceptions import BusinessLogicError, UnauthorizedAccess
from app.security import verify_password
from app.settings import settings


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.__db = db

    def login(self, data: models.AuthFields) -> schema.User:
        """
        Authenticate user and return user information.

        Args:
            data: Authentication fields (email, password)

        Returns:
            User object if authentication succeeds

        Raises:
            UnauthorizedAccess: If authentication fails or user is disabled
        """
        if not data.password:
            raise UnauthorizedAccess("Password is required")

        user = self.__db.query(schema.User).filter_by(email=data.email).first()

        if not user or not verify_password(data.password, user.password):
            raise UnauthorizedAccess("Invalid email or password")

        if user.disabled:
            raise BusinessLogicError("User account is disabled")

        return user

    def verify_session(self, session_token: str) -> schema.User | None:
        """
        Verify session token and return user.

        Args:
            session_token: Session token from cookie

        Returns:
            User object if token is valid, None otherwise
        """
        try:
            serializer = URLSafeTimedSerializer(secret_key=settings.secret_key)
            data = serializer.loads(session_token)
            user_id = data.get("user_id")
            if user_id:
                return self.__db.query(schema.User).filter_by(id=user_id).first()
        except Exception:
            pass
        return None
