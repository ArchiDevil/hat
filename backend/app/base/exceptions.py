"""Base exceptions for the application."""


class BaseQueryException(Exception):
    """Base exception for query layer errors."""

    pass


class BaseServiceException(Exception):
    """Base exception for service layer errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFound(BaseServiceException):
    """Raised when an entity is not found."""

    def __init__(self, entity_name: str, entity_id: int | str | None = None):
        if entity_id is None:
            # entity_name is actually the full message
            message = entity_name
        elif isinstance(entity_id, int):
            message = f"{entity_name} with id {entity_id} not found"
        else:
            message = f"{entity_name} '{entity_id}' not found"
        super().__init__(message)


class UnauthorizedAccess(BaseServiceException):
    """Raised when a user is not authorized to perform an action."""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)


class ValidationError(BaseServiceException):
    """Raised when validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


class BusinessLogicError(BaseServiceException):
    """Raised when business logic validation fails."""

    def __init__(self, message: str):
        super().__init__(message)
