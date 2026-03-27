"""Pydantic schemas for Registration Token entity."""

import datetime

from pydantic import ConfigDict

from app.base.schema import Identified


class RegistrationTokenResponse(Identified):
    """Response schema for registration token."""

    token: str
    created_at: datetime.datetime
    created_by: int

    model_config = ConfigDict(from_attributes=True)
