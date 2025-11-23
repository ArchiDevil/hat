import datetime
from typing import Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .models import TranslationMemory, TranslationMemoryRecord
from .schema import (
    MemorySubstitution,
    TranslationMemorySearchMode,
    TranslationMemorySearchResult,
)


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

    def search_memory_records(
        self,
        query: str,
        mode: TranslationMemorySearchMode,
        tm_id: int,
    ) -> list[TranslationMemorySearchResult]:
        if mode == TranslationMemorySearchMode.EXACT:
            return self._search_exact(query, tm_id)
        elif mode == TranslationMemorySearchMode.SIMILAR:
            return self._search_similar(query, tm_id)
        else:
            raise ValueError(f"Unsupported search mode: {mode}")

    def _search_exact(
        self, query: str, tm_id: int
    ) -> list[TranslationMemorySearchResult]:
        query_filter = TranslationMemoryRecord.source.ilike(f"%{query}%")

        records = self.__db.execute(
            select(TranslationMemoryRecord)
            .filter(query_filter, TranslationMemoryRecord.document_id == tm_id)
            .order_by(TranslationMemoryRecord.id)
            .limit(20)
        ).scalars()

        return [
            TranslationMemorySearchResult(
                id=record.id,
                source=record.source,
                target=record.target,
                similarity=None,
            )
            for record in records
        ]

    def _search_similar(
        self, query: str, tm_id: int
    ) -> list[TranslationMemorySearchResult]:
        # Use the same approach as get_substitutions but with different parameters
        similarity_func = func.similarity(TranslationMemoryRecord.source, query)

        # Set similarity threshold to 0.25 (25%) as required
        self.__db.execute(
            text("SET pg_trgm.similarity_threshold TO :threshold"),
            {"threshold": 0.25},
        )

        records = self.__db.execute(
            select(
                TranslationMemoryRecord.id,
                TranslationMemoryRecord.source,
                TranslationMemoryRecord.target,
                similarity_func,
            )
            .filter(
                TranslationMemoryRecord.source.op("%")(query),
                TranslationMemoryRecord.document_id == tm_id,
            )
            .order_by(similarity_func.desc())
            .limit(20)
        ).all()

        return [
            TranslationMemorySearchResult(
                id=record.id,
                source=record.source,
                target=record.target,
                similarity=record.similarity,
            )
            for record in records
        ]

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
