from enum import Enum
from typing import Literal

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


class LlmTranslatorSettings(BaseModel):
    type: Literal["llm"]
    api_key: str
    # base_api: str # reserved for universal OpenAI translation


class YandexTranslatorSettings(BaseModel):
    type: Literal["yandex"]
    folder_id: str
    oauth_token: str


MachineTranslationSettings = LlmTranslatorSettings | YandexTranslatorSettings


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
