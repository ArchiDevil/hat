import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.base.schema import IdentifiedTimestampedModel
from app.models import ShortUser


class GlossaryLoadFileResponse(BaseModel):
    glossary_id: int


class GlossarySchema(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryResponse(IdentifiedTimestampedModel):
    processing_status: str
    upload_time: datetime.datetime
    created_by_user: ShortUser
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecordSchema(IdentifiedTimestampedModel):
    comment: Optional[str]
    source: str
    target: str
    created_by_user: ShortUser

    glossary_id: int
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecordCreate(BaseModel):
    comment: Optional[str]
    source: str
    target: str

    model_config = ConfigDict(from_attributes=True)


class GlossaryRecordUpdate(BaseModel):
    comment: Optional[str]
    source: str
    target: str

    model_config = ConfigDict(from_attributes=True)
