from pydantic import BaseModel

class VoiceResponse(BaseModel):
    id: str
    languageCode: str
    languageShort: str
    voiceType: str
    displayName: str
    resourceId: str
    capturedAt: str | None = None

class VoiceListResponse(BaseModel):
    items: list[VoiceResponse]
    page: int
    pageSize: int
    total: int
