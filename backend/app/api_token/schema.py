import datetime

from pydantic import BaseModel, ConfigDict

from app.base.schema import Identified


class ApiTokenCreateRequest(BaseModel):
    name: str
    user_id: int
    expires_at: datetime.datetime | None = None


class ApiTokenResponse(Identified):
    name: str
    user_id: int
    created_by: int
    created_at: datetime.datetime
    expires_at: datetime.datetime | None
    last_used_at: datetime.datetime | None

    model_config = ConfigDict(from_attributes=True)


class ApiTokenCreatedResponse(ApiTokenResponse):
    token: str
