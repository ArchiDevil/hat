from enum import Enum

from pydantic import BaseModel, Field

from app.base.schema import Identified


class MemorySubstitution(BaseModel):
    source: str
    target: str
    similarity: float


class TranslationMemoryUsage(Enum):
    NEWEST = "newest"
    OLDEST = "oldest"


class TranslationMemory(Identified):
    name: str
    created_by: int


class TranslationMemoryWithRecordsCount(TranslationMemory):
    records_count: int


class TranslationMemoryRecord(Identified):
    source: str
    target: str


class TranslationMemoryCreationSettings(BaseModel):
    name: str = Field(min_length=1)


class TranslationMemorySearchMode(str, Enum):
    EXACT = "exact"
    SIMILAR = "similar"


class TranslationMemorySearchResult(TranslationMemoryRecord):
    similarity: float | None = None
