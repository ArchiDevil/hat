import io

import openpyxl
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.glossary.query import GlossaryQuery, NotFoundGlossaryExc
from app.glossary.schema import (
    GlossaryRecord,
    GlossaryRecordUpdate,
    GlossaryResponse,
    GlossaryScheme,
)


def create_glossary_from_file_controller(
    db: Session, file: UploadFile, user_id: int, glossary_name: str
):
    content = file.file.read()
    xlsx = io.BytesIO(content)
    workbook = openpyxl.load_workbook(xlsx)
    sheet = workbook["Sheet1"]
    glossary_scheme = GlossaryScheme(name=glossary_name)
    glossary_doc = GlossaryQuery(db).create_glossary(
        user_id=user_id, glossary=glossary_scheme
    )
    return sheet, glossary_doc


def list_glossary_controller(db: Session):
    glossaries = GlossaryQuery(db).list_glossary()
    return [GlossaryResponse.model_validate(glossary) for glossary in glossaries]


def list_glossary_records_controller(db: Session, glossary_id: int | None):
    records = GlossaryQuery(db).list_glossary_records(glossary_id)
    return [GlossaryRecord.model_validate(record) for record in records]


def retrieve_glossary_controller(glossary_doc_id: int, db: Session):
    try:
        doc = GlossaryQuery(db).get_glossary(glossary_doc_id)
        return GlossaryResponse.model_validate(doc)
    except NotFoundGlossaryExc:
        return None


def update_glossary_controller(glossary: GlossaryScheme, glossary_id: int, db: Session):
    try:
        return GlossaryQuery(db).update_glossary(glossary_id, glossary)
    except NotFoundGlossaryExc:
        return None


def update_glossary_record_controller(
    record_id: int, record: GlossaryRecordUpdate, db: Session
):
    try:
        return GlossaryQuery(db).update_record(record_id, record)
    except NotFoundGlossaryExc:
        return None
