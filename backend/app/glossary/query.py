from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import Glossary, GlossaryRecord
from app.base.exceptions import BaseQueryException
from app.glossary.models import ProcessingStatuses
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossaryRecordUpdate,
    GlossarySchema,
)
from app.linguistic.utils import postprocess_stemmed_segment, stem_sentence


class NotFoundGlossaryExc(BaseQueryException):
    """Not found glossary"""


class NotFoundGlossaryRecordExc(BaseQueryException):
    """Not found glossary record"""


class GlossaryQuery:
    """Contain query to Glossary & GlossaryRecord"""

    def __init__(self, db: Session):
        self.db = db

    def get_glossary(self, glossary_id: int) -> Glossary:
        glossary = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()  # type: ignore
        if glossary:
            return glossary
        raise NotFoundGlossaryExc()

    def get_glossaries(self, glossary_ids: list[int]) -> list[Glossary]:
        glossaries = (
            self.db.execute(select(Glossary).where(Glossary.id.in_(glossary_ids)))
            .scalars()
            .all()
        )
        if glossaries:
            return list(glossaries)
        raise NotFoundGlossaryExc()

    def get_glossary_record_by_id(self, record_id: int) -> GlossaryRecord:
        if (
            record := self.db.query(GlossaryRecord)
            .filter(GlossaryRecord.id == record_id)  # type: ignore
            .first()
        ):
            return record
        raise NotFoundGlossaryRecordExc()

    def get_glossary_records_for_phrase(
        self, phrase: str, glossary_ids: list[int]
    ) -> list[GlossaryRecord]:
        words = postprocess_stemmed_segment(stem_sentence(phrase))
        or_clauses = [GlossaryRecord.source.ilike(f"%{word}%") for word in words]
        records = self.db.execute(
            select(GlossaryRecord).where(
                or_(*or_clauses),
                GlossaryRecord.glossary_id.in_(glossary_ids),
            )
        ).scalars()

        output: list[GlossaryRecord] = []
        for record in records:
            glossary_words = record.stemmed_source.split(" ")
            found_words = [word for word in glossary_words if word in words]

            # naive approach to check if all words are found in a target phrase
            if len(found_words) == len(glossary_words):
                output.append(record)

        return output

    def list_glossary(self) -> list[Glossary]:
        return self.db.query(Glossary).order_by(Glossary.id).all()

    def list_glossary_records(
        self, glossary_id: int, page: int, page_records: int, search: str | None = None
    ):
        query = self.db.query(GlossaryRecord).filter(
            GlossaryRecord.glossary_id == glossary_id
        )
        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                (GlossaryRecord.source.ilike(like_pattern))
                | (GlossaryRecord.target.ilike(like_pattern))
            )
        selected_rows = (
            query.order_by(GlossaryRecord.id)
            .offset(page * page_records)
            .limit(page_records)
            .all()
        )
        total_rows = query.count()
        return selected_rows, total_rows

    def create_glossary(
        self,
        user_id: int,
        glossary: GlossarySchema,
        processing_status: str = ProcessingStatuses.IN_PROCESS,
    ) -> Glossary:
        glossary = Glossary(
            created_by=user_id,
            processing_status=processing_status,
            **glossary.model_dump(),
        )
        self.db.add(glossary)
        self.db.commit()
        return glossary

    def create_glossary_record(
        self,
        user_id: int,
        record: GlossaryRecordCreate,
        glossary_id: int,
    ) -> GlossaryRecord:
        glossary_record = GlossaryRecord(
            glossary_id=glossary_id,
            created_by=user_id,
            stemmed_source=" ".join(
                postprocess_stemmed_segment(stem_sentence(record.source))
            ),
            **record.model_dump(),
        )
        self.db.add(glossary_record)
        try:
            self.db.commit()
        except IntegrityError:
            raise NotFoundGlossaryExc
        return glossary_record

    def update_glossary(self, glossary_id: int, glossary: GlossarySchema) -> Glossary:
        result = (
            self.db.query(Glossary)
            .filter(Glossary.id == glossary_id)  # type: ignore
            .update(glossary.model_dump())  # type: ignore
        )
        if result:
            self.db.commit()
            return self.get_glossary(glossary_id)
        raise NotFoundGlossaryExc()

    def delete_glossary(self, glossary_id: int) -> bool:
        glossary = self.db.execute(
            select(Glossary).where(Glossary.id == glossary_id)  # type: ignore
        ).scalar_one_or_none()
        if not glossary:
            return False

        self.db.delete(glossary)
        self.db.commit()
        return True

    def update_glossary_processing_status(self, glossary_id: int) -> Glossary | None:
        doc = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()  # type: ignore
        if doc:
            doc.processing_status = ProcessingStatuses.DONE
            self.db.commit()
            return doc
        return None

    def bulk_create_glossary_record(self, records: list[GlossaryRecord]):
        self.db.add_all(records)
        self.db.commit()

    def update_record(self, record_id: int, record: GlossaryRecordUpdate):
        dump = record.model_dump()
        dump["stemmed_source"] = " ".join(
            postprocess_stemmed_segment(stem_sentence(record.source))
        )
        result = (
            self.db.query(GlossaryRecord)
            .filter(GlossaryRecord.id == record_id)  # type: ignore
            .update(dump)  # type: ignore
        )
        if result:
            self.db.commit()
            return self.get_glossary_record_by_id(record_id)
        raise NotFoundGlossaryRecordExc()

    def delete_record(self, record_id: int) -> bool:
        if (
            self.db.query(GlossaryRecord)
            .filter(GlossaryRecord.id == record_id)  # type: ignore
            .delete()
        ):
            self.db.commit()
            return True
        return False
