"""Background tasks for glossary processing."""

from sqlalchemy.orm import Session

from app.services import GlossaryService


def create_glossary_from_file_tasks(user_id: int, sheet, db: Session, glossary_id: int):
    """
    Background task to process glossary file and create records.

    Args:
        user_id: ID of user who uploaded the file
        sheet: XLSX sheet object
        db: Database session
        glossary_id: Glossary ID to add records to
    """
    service = GlossaryService(db)
    service.process_glossary_file(sheet, user_id, glossary_id)
