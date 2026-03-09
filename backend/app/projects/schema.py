from pydantic import BaseModel, ConfigDict, Field

from app.base.schema import Identified, IdentifiedTimestampedModel
from app.documents.models import TmMode
from app.documents.schema import DocumentWithRecordsCount
from app.glossary.schema import GlossaryResponse
from app.translation_memory.schema import TranslationMemory


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


class ProjectGlossary(Identified):
    glossaries: list[GlossaryResponse]

    model_config = ConfigDict(from_attributes=True)


class ProjectGlossaryUpdate(BaseModel):
    glossaries: list[int]

    model_config = ConfigDict(from_attributes=True)


class ProjectTmUpdateMode(Identified):
    mode: TmMode

    model_config = ConfigDict(from_attributes=True)


class ProjectTmUpdate(BaseModel):
    translation_memories: list[ProjectTmUpdateMode]

    model_config = ConfigDict(from_attributes=True)


class ProjectTm(BaseModel):
    memory: TranslationMemory
    mode: TmMode

    model_config = ConfigDict(from_attributes=True)


class ProjectTranslationMemory(Identified):
    translation_memories: list[ProjectTm]

    model_config = ConfigDict(from_attributes=True)


class DetailedProjectResponse(ProjectResponse):
    documents: list[DocumentWithRecordsCount]
    approved_records_count: int
    total_records_count: int
    approved_words_count: int
    total_words_count: int

    model_config = ConfigDict(from_attributes=True)
