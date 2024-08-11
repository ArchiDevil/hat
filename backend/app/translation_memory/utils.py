from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .models import TranslationMemoryRecord
from .schema import MemorySubstitution


def get_substitutions(
    source: str,
    tm_ids: list[int],
    db: Session,
    threshold: float = 0.7,
    count: int = 10,
) -> list[MemorySubstitution]:
    similarity_func = func.similarity(TranslationMemoryRecord.source, source)
    db.execute(
        text("SET pg_trgm.similarity_threshold TO :threshold"), {"threshold": threshold}
    )
    records = db.execute(
        select(
            TranslationMemoryRecord.source,
            TranslationMemoryRecord.target,
            similarity_func,
        )
        .filter(
            TranslationMemoryRecord.source.op("%")(source),
            TranslationMemoryRecord.document_id.in_(tm_ids),
        )
        .order_by(similarity_func.desc())
        .limit(count),
    ).all()

    return [
        MemorySubstitution(source=source, target=target, similarity=similarity)
        for (source, target, similarity) in records
    ]
