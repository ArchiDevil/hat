from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.glossary.controllers import (
    create_glossary_doc_from_file_controller,
    list_glossary_docs_controller,
    retrieve_glossary_doc_controller,
)
from app.glossary.schema import (
    GlossaryDocumentResponse,
    GlossaryLoadFileResponse,
)
from app.glossary.tasks import create_glossary_doc_from_file_tasks
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/glossary", tags=["glossary"], dependencies=[Depends(has_user_role)]
)


@router.get(
    "/docs",
    description="Get list glossary documents",
    response_model=list[GlossaryDocumentResponse],
    status_code=status.HTTP_200_OK,
)
def list_glossary_docs(db: Session = Depends(get_db)):
    return list_glossary_docs_controller(db)


@router.get(
    "/docs/{glossary_doc_id}",
    description="Get a single glossary documents",
    response_model=GlossaryDocumentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary docs requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary document id: 1, not found"}
                }
            },
        },
    },
)
def retrieve_glossary_doc(glossary_doc_id: int, db: Session = Depends(get_db)):
    glossary_doc_response = retrieve_glossary_doc_controller(glossary_doc_id, db)
    if glossary_doc_response:
        return glossary_doc_response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary document id:{glossary_doc_id}, not found",
    )


@router.post(
    "/load_file",
    description="Load xlsx glossary file",
    response_model=GlossaryLoadFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary_doc_from_file(
    user_id: Annotated[int, Depends(get_current_user_id)],
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    sheet, glossary_doc = create_glossary_doc_from_file_controller(db, file, user_id)
    background_tasks.add_task(
        create_glossary_doc_from_file_tasks,
        sheet=sheet,
        db=db,
        glossary_doc_id=glossary_doc.id,
    )
    return GlossaryLoadFileResponse(glossary_doc_id=glossary_doc.id)
