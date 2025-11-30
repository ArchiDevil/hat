from datetime import datetime

from pydantic import BaseModel, Field

from app.base.schema import Identified


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, description="Comment text")


class CommentUpdate(BaseModel):
    text: str = Field(min_length=1, description="Updated comment text")


class CommentResponse(Identified):
    text: str
    updated_at: datetime
    author_id: int
    document_record_id: int
