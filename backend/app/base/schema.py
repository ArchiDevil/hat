import datetime

from pydantic import BaseModel


class Identified(BaseModel):
    id: int


class IdentifiedTimestampedModel(Identified):
    created_at: datetime.datetime
    updated_at: datetime.datetime
