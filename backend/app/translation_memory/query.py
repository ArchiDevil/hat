import datetime
from typing import Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.translation_memory import schema

from .models import TranslationMemory, TranslationMemoryRecord


class TranslationMemoryQuery:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_memories(self) -> Iterable[TranslationMemory]:
        return self.__db.execute(
            select(TranslationMemory).order_by(TranslationMemory.id)
        ).scalars()

    def get_memories_by_id(self, ids: Iterable[int]) -> Iterable[TranslationMemory]:
        return self.__db.execute(
            select(TranslationMemory).where(TranslationMemory.id.in_(ids))
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
        self,
        memory_id: int,
        page: int,
        page_records: int,
        query: str | None,
    ) -> list[schema.TranslationMemoryRecord]:
        filters = [TranslationMemoryRecord.document_id == memory_id]
        if query:
            filters.append(TranslationMemoryRecord.source.ilike(f"%{query}%"))

        return [
            schema.TranslationMemoryRecord(
                id=scalar.id, source=scalar.source, target=scalar.target
            )
            for scalar in self.__db.execute(
                select(TranslationMemoryRecord)
                .filter(*filters)
                .order_by(TranslationMemoryRecord.id)
                .offset(page_records * page)
                .limit(page_records)
            ).scalars()
        ]

    def get_memory_records_paged_similar(
        self,
        memory_id: int,
        page_records: int,
        query: str,
    ) -> list[schema.TranslationMemoryRecordWithSimilarity]:
        # Use the same approach as get_substitutions but with different parameters
        similarity_func = func.similarity(TranslationMemoryRecord.source, query)

        # Set similarity threshold to 0.25 (25%) as required
        self.__db.execute(
            text("SET pg_trgm.similarity_threshold TO :threshold"),
            {"threshold": 0.25},
        )

        return [
            schema.TranslationMemoryRecordWithSimilarity(
                id=scalar.id,
                source=scalar.source,
                target=scalar.target,
                similarity=scalar.similarity,
            )
            for scalar in self.__db.execute(
                select(
                    TranslationMemoryRecord.id,
                    TranslationMemoryRecord.source,
                    TranslationMemoryRecord.target,
                    similarity_func,
                )
                .filter(
                    TranslationMemoryRecord.document_id == memory_id,
                    TranslationMemoryRecord.source.op("%")(query),
                )
                .order_by(similarity_func.desc())
                .limit(page_records)
            ).all()
        ]

    def get_substitutions(
        self,
        source: str,
        tm_ids: list[int],
        threshold: float = 0.75,
        count: int = 10,
    ) -> list[schema.MemorySubstitution]:
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
            schema.MemorySubstitution(
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

    def add_or_update_record(self, document_id: int, source: str, target: str):
        record = self.__db.execute(
            select(TranslationMemoryRecord)
            .where(
                TranslationMemoryRecord.document_id == document_id,
                TranslationMemoryRecord.source == source,
            )
            .order_by(TranslationMemoryRecord.id.desc()),
        ).scalar_one_or_none()

        if not record:
            self.__db.add(
                TranslationMemoryRecord(
                    document_id=document_id,
                    source=source,
                    target=target,
                    creation_date=datetime.datetime.now(datetime.UTC),
                    change_date=datetime.datetime.now(datetime.UTC),
                )
            )
        else:
            record.target = target
            record.change_date = datetime.datetime.now(datetime.UTC)

        self.__db.commit()
