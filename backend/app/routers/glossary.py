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
    create_glossary_from_file_controller,
    create_glossary_record_controller,
    delete_glossary_controller,
    delete_glossary_record_controller,
    list_glossary_controller,
    list_glossary_records_controller,
    retrieve_glossary_controller,
    update_glossary_controller,
    update_glossary_record_controller,
)
from app.glossary.models import ProcessingStatuses
from app.glossary.query import GlossaryQuery
from app.glossary.schema import (
    GlossaryLoadFileResponse,
    GlossaryRecordCreate,
    GlossaryRecordSchema,
    GlossaryRecordUpdate,
    GlossaryResponse,
    GlossaryScheme,
)
from app.glossary.tasks import create_glossary_from_file_tasks
from app.models import StatusMessage
from app.user.depends import get_current_user_id, has_user_role

router = APIRouter(
    prefix="/glossary", tags=["glossary"], dependencies=[Depends(has_user_role)]
)


@router.get(
    "/",
    description="Get list glossary",
    response_model=list[GlossaryResponse],
    status_code=status.HTTP_200_OK,
)
def list_glossary(db: Session = Depends(get_db)):
    return list_glossary_controller(db)


@router.get(
    path="/{glossary_id}",
    description="Get a single glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {"example": {"detail": "Glossary id: 1, not found"}}
            },
        },
    },
)
def retrieve_glossary(glossary_id: int, db: Session = Depends(get_db)):
    if response := retrieve_glossary_controller(glossary_id, db):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary id:{glossary_id}, not found",
    )


@router.post(
    "/",
    description="Create glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary(
    glossary: GlossaryScheme,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return GlossaryQuery(db).create_glossary(
        glossary=glossary,
        processing_status=ProcessingStatuses.DONE,
        user_id=current_user_id,
    )


@router.put(
    path="/{glossary_id}",
    description="Update a single glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {"example": {"detail": "Glossary id: 1, not found"}}
            },
        },
    },
)
def update_glossary(
    glossary_id: int, glossary: GlossaryScheme, db: Session = Depends(get_db)
):
    if response := update_glossary_controller(
        db=db, glossary_id=glossary_id, glossary=glossary
    ):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary id:{glossary_id}, not found",
    )


@router.delete(
    path="/{glossary_id}",
    description="Delete a single glossary",
    response_model=StatusMessage,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary requested by id",
            "content": {
                "application/json": {"example": {"detail": "Glossary id: 1, not found"}}
            },
        },
    },
)
def delete_glossary(glossary_id: int, db: Session = Depends(get_db)):
    if response := delete_glossary_controller(glossary_id, db):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary id:{glossary_id}, not found",
    )


@router.get(
    "/{glossary_id}/records",
    description="Get list glossary record ",
    response_model=list[GlossaryRecordSchema],
    status_code=status.HTTP_200_OK,
)
def list_records(glossary_id: int | None = None, db: Session = Depends(get_db)):
    return list_glossary_records_controller(db, glossary_id)


@router.post(
    "/{glossary_id}/records",
    description="Create glossary record ",
    response_model=GlossaryRecordSchema,
    status_code=status.HTTP_200_OK,
)
def create_glossary_record(
    glossary_id: int, record: GlossaryRecordCreate, db: Session = Depends(get_db)
):
    if response := create_glossary_record_controller(glossary_id, record, db):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary id:{glossary_id}, not found",
    )


@router.put(
    path="/records/{record_id}",
    description="Update a single glossary record",
    response_model=GlossaryRecordSchema,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary record requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary record id: 1, not found"}
                }
            },
        },
    },
)
def update_glossary_record(
    record_id: int, record: GlossaryRecordUpdate, db: Session = Depends(get_db)
):
    if response := update_glossary_record_controller(record_id, record, db):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary record id:{record_id}, not found",
    )


@router.delete(
    path="/records/{record_id}",
    description="Delete a single glossary record",
    response_model=StatusMessage,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Glossary record requested by id",
            "content": {
                "application/json": {
                    "example": {"detail": "Glossary record id: 1, not found"}
                }
            },
        },
    },
)
def delete_glossary_record(record_id: int, db: Session = Depends(get_db)):
    if response := delete_glossary_record_controller(record_id, db):
        return response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Glossary record id:{record_id}, not found",
    )


@router.post(
    "/load_file",
    description="Load xlsx glossary file",
    response_model=GlossaryLoadFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary_from_file(
    user_id: Annotated[int, Depends(get_current_user_id)],
    glossary_name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    sheet, glossary = create_glossary_from_file_controller(
        db=db, file=file, user_id=user_id, glossary_name=glossary_name
    )
    background_tasks.add_task(
        create_glossary_from_file_tasks,
        sheet=sheet,
        db=db,
        glossary_id=glossary.id,
    )
    return GlossaryLoadFileResponse(glossary_id=glossary.id)
