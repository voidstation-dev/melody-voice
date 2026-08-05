from pydantic import BaseModel, Field

class CreateTTSJobRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500000)
    voiceType: str = Field(min_length=1, max_length=150)
    resourceId: str | None = Field(default=None)
    rate: float = Field(default=1.0, ge=0.5, le=2.0)
    sourceFileName: str | None = Field(default=None)
    sourceFileSize: int | None = Field(default=None)
    batchId: str | None = Field(default=None)
    batchPosition: int | None = Field(default=None)

class TTSJobResponse(BaseModel):
    id: str
    text: str
    textPreview: str
    voiceType: str
    voiceDisplayName: str
    resourceId: str | None
    rate: float
    providerId: str | None = None
    status: str
    progress: int | None = None
    batchId: str | None = None
    batchPosition: int | None = None
    sourceFileName: str | None = None
    sourceFileSize: int | None = None
    audioUrl: str | None = None
    audioDuration: float | None = None
    downloadUrl: str | None = None
    fileSize: int | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    createdAt: str
    startedAt: str | None = None
    updatedAt: str
    completedAt: str | None = None

class BatchJobCreateResponse(BaseModel):
    batchId: str
    jobs: list[TTSJobResponse]

class TTSJobListResponse(BaseModel):
    items: list[TTSJobResponse]
    page: int
    pageSize: int
    total: int
