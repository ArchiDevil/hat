from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.glossary.controllers import (
    create_glossary_doc_from_file_controller,
    list_glossary_docs_controller,
)
from app.glossary.schema import GlossaryDocumentListResponse, GlossaryLoadFileResponse
from app.glossary.tasks import create_glossary_doc_from_file_tasks
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/glossary", tags=["glossary"], dependencies=[Depends(has_user_role)]
)


@router.get(
    "/",
    description="Get list glossary documents",
    response_model=GlossaryDocumentListResponse,
    status_code=status.HTTP_200_OK,
)
def list_glossary_docs(db: Session = Depends(get_db)):
    glossaries = list_glossary_docs_controller(db)
    return GlossaryDocumentListResponse(glossaries=glossaries)


@router.post(
    "/load_file",
    description="Load xlsx glossary file",
    response_model=GlossaryLoadFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary_doc_from_file(
    user_id: Annotated[int, Depends(get_current_user_id)],
    background_tasks: BackgroundTasks,
    uploaded_file: UploadFile,
    db: Session = Depends(get_db),
):
    sheet, glossary_doc = create_glossary_doc_from_file_controller(
        db, uploaded_file, user_id
    )
    background_tasks.add_task(
        create_glossary_doc_from_file_tasks,
        sheet=sheet,
        db=db,
        glossary_doc_id=glossary_doc.id,
    )
    return GlossaryLoadFileResponse(glossary_doc_id=glossary_doc.id)
