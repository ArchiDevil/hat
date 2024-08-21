from typing import Type

from sqlalchemy.orm import Session

from app import Glossary, GlossaryRecord
from app.base.exceptions import BaseQueryException
from app.glossary.models import ProcessingStatuses


class NotFoundGlossaryExc(BaseQueryException):
    """Not found glossary doc"""


class GlossaryQuery:
    """Contain query to Glossary & GlossaryRecord"""

    def __init__(self, db: Session):
        self.db = db

    def get_glossary(self, glossary_id: int) -> Type[Glossary]:
        glossary = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()
        if glossary:
            return glossary
        raise NotFoundGlossaryExc()

    def list_glossary(self) -> list[Type[Glossary]]:
        return self.db.query(Glossary).order_by(Glossary.id).all()

    def list_glossary_records(
        self, glossary_id: int | None = None
    ) -> list[Type[GlossaryRecord]]:
        if glossary_id:
            return (
                self.db.query(GlossaryRecord)
                .filter(GlossaryRecord.glossary_id == glossary_id)
                .order_by(GlossaryRecord.id)
                .all()
            )
        return self.db.query(GlossaryRecord).order_by(GlossaryRecord.id).all()

    def create_glossary(self, user_id: int, glossary_name: str) -> Glossary:
        glossary = Glossary(
            user_id=user_id,
            name=glossary_name,
        )
        self.db.add(glossary)
        self.db.commit()
        return glossary

    def create_glossary_record(
        self,
        author: str,
        source: str,
        target: str,
        glossary_id: int,
        comment: str | None = None,
    ) -> GlossaryRecord:
        glossary_record = GlossaryRecord(
            author=author,
            comment=comment,
            source=source,
            target=target,
            glossary_id=glossary_id,
        )
        self.db.add(glossary_record)
        self.db.commit()
        return glossary_record

    def update_glossary(self, glossary_id: int, glossary: Glossary) -> Type[Glossary]:
        result = (
            self.db.query(Glossary)
            .filter(Glossary.id == glossary_id)
            .update(glossary.model_dump())
        )
        if result:
            self.db.commit()
            return self.get_glossary(glossary_id)
        raise NotFoundGlossaryExc()

    def update_glossary_processing_status(
        self, glossary_id: int
    ) -> Type[Glossary] | None:
        doc = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()
        if doc:
            doc.processing_status = ProcessingStatuses.DONE
            self.db.commit()
            return doc
        return None

    def bulk_create_glossary_record(self, records: list[GlossaryRecord]):
        self.db.add_all(records)
        self.db.commit()
