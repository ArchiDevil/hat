import io

import openpyxl
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.glossary.query import GlossaryDocsQuery, NotFoundGlossaryDocExc
from app.glossary.schema import GlossaryDocument, GlossaryDocumentResponse


def create_glossary_doc_from_file_controller(
    db: Session, file: UploadFile, user_id: int, document_name: str
):
    content = file.file.read()
    xlsx = io.BytesIO(content)
    workbook = openpyxl.load_workbook(xlsx)
    sheet = workbook["Sheet1"]
    glossary_doc = GlossaryDocsQuery(db).create_glossary_doc(
        user_id=user_id, document_name=document_name
    )
    return sheet, glossary_doc


def list_glossary_docs_controller(db: Session):
    glossaries = GlossaryDocsQuery(db).list_glossary_docs()
    return [
        GlossaryDocumentResponse.model_validate(glossary) for glossary in glossaries
    ]


def retrieve_glossary_doc_controller(glossary_doc_id: int, db: Session):
    try:
        doc = GlossaryDocsQuery(db).get_glossary_doc(glossary_doc_id)
        return GlossaryDocumentResponse.model_validate(doc)
    except NotFoundGlossaryDocExc:
        return None


def update_glossary_doc_controller(
    document: GlossaryDocument, document_id: int, db: Session
):
    try:
        return GlossaryDocsQuery(db).update_doc(document_id, document)
    except NotFoundGlossaryDocExc:
        return None
