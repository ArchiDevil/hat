from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr

from app.base.schema import Identified


class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

    @classmethod
    def get_values(cls):
        return tuple(role.value for role in cls)


class MachineTranslationSettings(BaseModel):
    # Yandex only for now
    # source_language: str
    # target_language: str
    folder_id: str
    oauth_token: str


class StatusMessage(BaseModel):
    message: str


class UserFields(BaseModel):
    username: str
    email: EmailStr
    role: UserRole
    disabled: bool


class UserToCreate(UserFields):
    password: str


class ShortUser(Identified):
    username: str
    model_config = ConfigDict(from_attributes=True)


class User(Identified, UserFields):
    pass


class AuthFields(BaseModel):
    email: EmailStr
    password: str
    remember: bool
