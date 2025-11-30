from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.base.schema import Identified
from app.models import ShortUser


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, description="Comment text")


class CommentUpdate(BaseModel):
    text: str = Field(min_length=1, description="Updated comment text")


class CommentResponse(Identified):
    text: str
    updated_at: datetime
    record_id: int
    created_by_user: ShortUser

    model_config = ConfigDict(from_attributes=True)
