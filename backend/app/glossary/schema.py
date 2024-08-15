import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.base.schema import IdentifiedTimestampedModel


class GlossaryLoadFileResponse(BaseModel):
    glossary_doc_id: int


class GlossaryDocument(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class GlossaryRecord(IdentifiedTimestampedModel):
    author: str
    comment: Optional[str]
    source: str
    target: str

    document_id: int
    model_config = ConfigDict(from_attributes=True)


class GlossaryDocumentResponse(IdentifiedTimestampedModel):
    processing_status: str
    upload_time: datetime.datetime
    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)
