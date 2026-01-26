from sqlalchemy import select
from sqlalchemy.orm import Session

from app.base.exceptions import BaseQueryException
from app.documents.models import DocumentRecord
from app.documents.schema import DocumentRecordUpdate


class NotFoundDocumentRecordExc(BaseQueryException):
    """Exception raised when document record not found"""


class RecordsQuery:
    def __init__(self, db: Session) -> None:
        self.__db = db

    def get_record(self, record_id: int) -> DocumentRecord | None:
        return self.__db.execute(
            select(DocumentRecord).filter(DocumentRecord.id == record_id)
        ).scalar_one_or_none()

    def update_record(
        self, record_id: int, data: DocumentRecordUpdate
    ) -> DocumentRecord:
        record = self.get_record(record_id)
        if not record:
            raise NotFoundDocumentRecordExc()

        record.target = data.target
        if data.approved is not None:
            record.approved = data.approved

        self.__db.commit()
        return record
