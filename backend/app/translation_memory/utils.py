from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models, schema


def get_substitutions(
    source: str,
    tmx_ids: list[int],
    db: Session,
    threshold: float = 0.7,
    count: int = 10,
) -> list[models.XliffSubstitution]:
    similarity_func = func.similarity(schema.TmxRecord.source, source)
    db.execute(
        text("SET pg_trgm.similarity_threshold TO :threshold"), {"threshold": threshold}
    )
    records = db.execute(
        select(schema.TmxRecord.source, schema.TmxRecord.target, similarity_func)
        .filter(
            schema.TmxRecord.source.op("%")(source),
            schema.TmxRecord.document_id.in_(tmx_ids),
        )
        .order_by(similarity_func.desc())
        .limit(count),
    ).all()

    return [
        models.XliffSubstitution(source=source, target=target, similarity=similarity)
        for (source, target, similarity) in records
    ]
