import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.base.schema import IdentifiedTimestampedModel


class GlossaryLoadFileResponse(BaseModel):
    glossary_id: int


class GlossaryScheme(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryResponse(IdentifiedTimestampedModel):
    processing_status: str
    upload_time: datetime.datetime
    created_by: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecordSchema(IdentifiedTimestampedModel):
    created_by: int
    comment: Optional[str]
    source: str
    target: str

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
