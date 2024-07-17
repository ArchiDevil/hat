import io

import openpyxl
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.glossary.query import create_glossary_doc


def create_glossary_doc_from_file_controller(
    db: Session, uploaded_file: UploadFile, user_id: int
):
    content = uploaded_file.file.read()
    xlsx = io.BytesIO(content)
    workbook = openpyxl.load_workbook(xlsx)
    sheet = workbook["Sheet1"]
    glossary_doc = create_glossary_doc(
        db=db, document_name=uploaded_file.filename, user_id=user_id
    )
    return sheet, glossary_doc
