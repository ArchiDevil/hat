from pydantic import BaseModel, ConfigDict, Field

from app.base.schema import IdentifiedTimestampedModel
from app.documents.schema import DocumentWithRecordsCount


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(IdentifiedTimestampedModel):
    name: str
    created_by: int

    model_config = ConfigDict(from_attributes=True)


class DetailedProjectResponse(ProjectResponse):
    documents: list[DocumentWithRecordsCount]
    approved_records_count: int
    total_records_count: int
    approved_words_count: int
    total_words_count: int

    model_config = ConfigDict(from_attributes=True)
