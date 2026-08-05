from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomVoiceResponse(BaseModel):
    id: str
    display_name: str
    transcript: str
    consent_given: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomVoiceListResponse(BaseModel):
    items: list[CustomVoiceResponse]
    total: int
