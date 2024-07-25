from pydantic import BaseModel


class MemorySubstitution(BaseModel):
    source: str
    target: str
    similarity: float
