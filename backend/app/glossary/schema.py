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
    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecord(IdentifiedTimestampedModel):
    author: str
    comment: Optional[str]
    source: str
    target: str

    glossary_id: int
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecordUpdate(BaseModel):
    author: str
    comment: Optional[str]
    source: str
    target: str

    model_config = ConfigDict(from_attributes=True)
