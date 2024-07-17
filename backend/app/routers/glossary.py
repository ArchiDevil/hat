from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.glossary.controllers import create_glossary_doc_from_file_controller
from app.glossary.tasks import create_glossary_doc_from_file_tasks
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/glossary", tags=["glossary"], dependencies=[Depends(has_user_role)]
)


@router.post("/load_file", description="Load xlsx glossary file")
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
    return {"message": "Notification sent in the background"}
