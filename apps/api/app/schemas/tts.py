from pydantic import BaseModel, Field

class CreateTTSJobRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    voiceType: str = Field(min_length=1, max_length=150)
    resourceId: str | None = Field(default=None)
    rate: float = Field(default=1.0, ge=0.5, le=2.0)

class TTSJobResponse(BaseModel):
    id: str
    text: str
    textPreview: str
    voiceType: str
    voiceDisplayName: str
    resourceId: str | None
    rate: float
    status: str
    progress: int | None = None
    audioUrl: str | None = None
    downloadUrl: str | None = None
    fileSize: int | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    createdAt: str
    updatedAt: str
    completedAt: str | None = None

class TTSJobListResponse(BaseModel):
    items: list[TTSJobResponse]
    page: int
    pageSize: int
    total: int
