from pydantic import BaseModel, ConfigDict, Field

from app.base.schema import Identified


class MemorySubstitution(BaseModel):
    source: str
    target: str
    similarity: float


class TranslationMemory(Identified):
    name: str
    created_by: int

    model_config = ConfigDict(from_attributes=True)


class TranslationMemoryWithRecordsCount(TranslationMemory):
    records_count: int


class TranslationMemoryRecord(Identified):
    source: str
    target: str


class TranslationMemoryListResponse(BaseModel):
    records: list[TranslationMemoryRecord]
    page: int
    total_records: int


class TranslationMemoryRecordWithSimilarity(TranslationMemoryRecord):
    similarity: float


class TranslationMemoryListSimilarResponse(BaseModel):
    records: list[TranslationMemoryRecordWithSimilarity]
    page: int
    total_records: int


class TranslationMemoryCreationSettings(BaseModel):
    name: str = Field(min_length=1)
