import io

import openpyxl
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.glossary.query import (
    GlossaryQuery,
    NotFoundGlossaryExc,
    NotFoundGlossaryRecordExc,
)
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossaryRecordSchema,
    GlossaryRecordUpdate,
    GlossaryResponse,
    GlossaryScheme,
)
from app.models import StatusMessage


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
    return [GlossaryRecordSchema.model_validate(record) for record in records]


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


def delete_glossary_controller(glossary_id: int, db: Session):
    if GlossaryQuery(db).delete_glossary(glossary_id):
        return StatusMessage(message="Deleted")


def update_glossary_record_controller(
    record_id: int, record: GlossaryRecordUpdate, db: Session
):
    try:
        return GlossaryQuery(db).update_record(record_id, record)
    except NotFoundGlossaryRecordExc:
        return None


def create_glossary_record_controller(
    glossary_id: int, record: GlossaryRecordCreate, db: Session
):
    try:
        return GlossaryQuery(db).create_glossary_record(
            glossary_id=glossary_id, record=record
        )
    except NotFoundGlossaryExc:
        return None


def delete_glossary_record_controller(record_id: int, db: Session):
    if GlossaryQuery(db).delete_record(record_id):
        return StatusMessage(message="Deleted")
