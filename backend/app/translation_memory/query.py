from typing import Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .models import TranslationMemory, TranslationMemoryRecord
from .schema import MemorySubstitution


class TranslationMemoryQuery:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_memories(self) -> Iterable[TranslationMemory]:
        return self.__db.execute(
            select(TranslationMemory).order_by(TranslationMemory.id)
        ).scalars()

    def get_memory(self, id_: int) -> TranslationMemory | None:
        return self.__db.execute(
            select(TranslationMemory).where(TranslationMemory.id == id_)
        ).scalar_one_or_none()

    def get_memory_records_count(self, memory_id: int) -> int:
        return self.__db.execute(
            select(func.count(TranslationMemoryRecord.id)).filter(
                TranslationMemoryRecord.document_id == memory_id
            )
        ).scalar_one()

    def get_memory_records_paged(
        self, memory_id: int, page: int, page_records: int
    ) -> Iterable[TranslationMemoryRecord]:
        return self.__db.execute(
            select(TranslationMemoryRecord)
            .filter(TranslationMemoryRecord.document_id == memory_id)
            .order_by(TranslationMemoryRecord.id)
            .offset(page_records * page)
            .limit(page_records)
        ).scalars()

    def get_substitutions(
        self,
        source: str,
        tm_ids: list[int],
        threshold: float = 0.75,
        count: int = 10,
    ) -> list[MemorySubstitution]:
        similarity_func = func.similarity(TranslationMemoryRecord.source, source)
        self.__db.execute(
            text("SET pg_trgm.similarity_threshold TO :threshold"),
            {"threshold": threshold},
        )
        records = self.__db.execute(
            select(
                TranslationMemoryRecord.source,
                TranslationMemoryRecord.target,
                similarity_func,
            )
            .filter(
                TranslationMemoryRecord.source.op("%")(source),
                TranslationMemoryRecord.document_id.in_(tm_ids),
            )
            .order_by(similarity_func.desc())
            .limit(count),
        ).all()

        return [
            MemorySubstitution(
                source=record.source, target=record.target, similarity=record.similarity
            )
            for record in records
        ]

    def add_memory(
        self, name: str, created_by: int, records: list[TranslationMemoryRecord]
    ) -> TranslationMemory:
        doc = TranslationMemory(name=name, created_by=created_by, records=records)
        self.__db.add(doc)
        self.__db.commit()
        return doc

    def delete_memory(self, memory: TranslationMemory):
        self.__db.delete(memory)
        self.__db.commit()
