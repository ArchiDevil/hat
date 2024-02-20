from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db_fastapi import get_db
from app.schema import TmxDocument, TmxRecord
from app.tmx import extract_tmx_content


class TmxFile(BaseModel):
    id: int
    name: str


class TmxFileRecord(BaseModel):
    id: int
    source: str
    target: str


class TmxFileWithRecords(TmxFile):
    records: list[TmxFileRecord]


class StatusMessage(BaseModel):
    message: str


router = APIRouter(prefix="/tmx", tags=["tmx"])


@router.get("/")
def get_tmxs(db: Session = Depends(get_db)) -> list[TmxFile]:
    docs = db.query(TmxDocument).all()
    return [TmxFile(id=doc.id, name=doc.name) for doc in docs]


@router.get("/{tmx_id}")
def get_tmx(tmx_id: int, db: Session = Depends(get_db)) -> TmxFileWithRecords:
    doc = db.query(TmxDocument).filter(TmxDocument.id == tmx_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return TmxFileWithRecords(
        id=doc.id,
        name=doc.name,
        records=[
            TmxFileRecord(id=record.id, source=record.source, target=record.target)
            for record in doc.records
        ],
    )


@router.post("/")
async def create_tmx(
    file: Annotated[UploadFile, File()], db: Session = Depends(get_db)
) -> TmxFile:
    name = file.filename
    tmx_data = await file.read()
    tmx_data = extract_tmx_content(tmx_data)

    doc = TmxDocument(name=name)
    db.add(doc)
    db.commit()

    for source, target in tmx_data:
        doc.records.append(TmxRecord(source=source, target=target))
    db.commit()

    new_doc = db.query(TmxDocument).filter(TmxDocument.id == doc.id).first()
    assert new_doc

    return TmxFile(id=new_doc.id, name=new_doc.name)


@router.delete("/{tmx_id}")
def delete_tmx(tmx_id: int, db: Session = Depends(get_db)) -> StatusMessage:
    doc = db.query(TmxDocument).filter(TmxDocument.id == tmx_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    db.delete(doc)
    db.commit()
    return StatusMessage(message="Deleted")
