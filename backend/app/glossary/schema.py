import datetime

from pydantic import BaseModel

from app.base.schema import IdentifiedTimestampedModel


class GlossaryLoadFileResponse(BaseModel):
    glossary_doc_id: int


class GlossaryDocumentResponse(IdentifiedTimestampedModel):
    processing_status: str
    upload_time: datetime.datetime
    user_id: int

    class Config:
        from_attributes = True


class GlossaryDocumentListResponse(BaseModel):
    glossaries: list[GlossaryDocumentResponse]

    class Config:
        from_attributes = True
