from typing import Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import Glossary, GlossaryRecord
from app.base.exceptions import BaseQueryException
from app.glossary.models import ProcessingStatuses
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossaryRecordUpdate,
    GlossaryScheme,
)


class NotFoundGlossaryExc(BaseQueryException):
    """Not found glossary"""


class NotFoundGlossaryRecordExc(BaseQueryException):
    """Not found glossary record"""


class GlossaryQuery:
    """Contain query to Glossary & GlossaryRecord"""

    def __init__(self, db: Session):
        self.db = db

    def get_glossary(self, glossary_id: int) -> Type[Glossary]:
        glossary = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()  # type: ignore
        if glossary:
            return glossary
        raise NotFoundGlossaryExc()

    def get_glossary_record(self, record_id: int) -> Type[GlossaryRecord]:
        if (
            record := self.db.query(GlossaryRecord)
            .filter(GlossaryRecord.id == record_id)  # type: ignore
            .first()
        ):
            return record
        raise NotFoundGlossaryRecordExc()

    def list_glossary(self) -> list[Type[Glossary]]:
        return self.db.query(Glossary).order_by(Glossary.id).all()

    def list_glossary_records(
        self, glossary_id: int | None = None
    ) -> list[Type[GlossaryRecord]]:
        if glossary_id:
            return (
                self.db.query(GlossaryRecord)
                .filter(GlossaryRecord.glossary_id == glossary_id)  # type: ignore
                .order_by(GlossaryRecord.id)
                .all()
            )
        return self.db.query(GlossaryRecord).order_by(GlossaryRecord.id).all()

    def create_glossary(
        self,
        user_id: int,
        glossary: GlossaryScheme,
        processing_status: str = ProcessingStatuses.IN_PROCESS,
    ) -> Glossary:
        glossary = Glossary(
            user_id=user_id,
            processing_status=processing_status,
            **glossary.model_dump(),
        )
        self.db.add(glossary)
        self.db.commit()
        return glossary

    def create_glossary_record(
        self,
        record: GlossaryRecordCreate,
        glossary_id: int,
    ) -> GlossaryRecord:
        glossary_record = GlossaryRecord(
            glossary_id=glossary_id,
            **record.model_dump(),
        )
        self.db.add(glossary_record)
        try:
            self.db.commit()
        except IntegrityError:
            raise NotFoundGlossaryExc
        return glossary_record

    def update_glossary(
        self, glossary_id: int, glossary: GlossaryScheme
    ) -> Type[Glossary]:
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
        if (
            self.db.query(Glossary)
            .filter(Glossary.id == glossary_id)  # type: ignore
            .delete()
        ):
            self.db.commit()
            return True
        return False

    def update_glossary_processing_status(
        self, glossary_id: int
    ) -> Type[Glossary] | None:
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
        result = (
            self.db.query(GlossaryRecord)
            .filter(GlossaryRecord.id == record_id)  # type: ignore
            .update(record.model_dump())  # type: ignore
        )
        if result:
            self.db.commit()
            return self.get_glossary_record(record_id)
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
