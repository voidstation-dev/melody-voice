from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_async_session
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.schemas.tts import CreateTTSJobRequest, TTSJobListResponse, TTSJobResponse
from app.services.tts_service import create_tts_job, get_job_by_id, list_jobs
from app.workers.tts_worker import execute_tts_job_step

router = APIRouter()

def serialize_job(job: TTSJobModel) -> TTSJobResponse:
    text_prev = job.text[:80] + "..." if len(job.text) > 80 else job.text
    return TTSJobResponse(
        id=job.id,
        text=job.text,
        textPreview=text_prev,
        voiceType=job.voice_type,
        voiceDisplayName=job.voice_display_name,
        resourceId=job.resource_id,
        rate=job.rate,
        status=job.status,
        progress=job.progress,
        audioUrl=f"/api/v1/tts/jobs/{job.id}/audio" if job.status == "completed" else None,
        downloadUrl=f"/api/v1/tts/jobs/{job.id}/download" if job.status == "completed" else None,
        fileSize=job.audio_file_size,
        errorCode=job.error_code,
        errorMessage=job.error_message,
        createdAt=job.created_at.isoformat(),
        updatedAt=job.updated_at.isoformat(),
        completedAt=job.completed_at.isoformat() if job.completed_at else None,
    )

@router.post("/tts/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=TTSJobResponse)
async def create_job_endpoint(
    req: CreateTTSJobRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    voices = provider.list_voices()
    matched = next((v for v in voices if v.voice_type == req.voiceType), None)
    
    if not matched:
        raise HTTPException(status_code=422, detail="VOICE_NOT_FOUND: Selected voice type does not exist in catalog")

    job = await create_tts_job(
        session,
        text=req.text,
        voice_type=req.voiceType,
        voice_display_name=matched.display_name,
        language_code=matched.language_code,
        resource_id=matched.resource_id,
        rate=req.rate,
    )

    background_tasks.add_task(execute_tts_job_step, job.id, session)
    return serialize_job(job)

@router.get("/tts/jobs/{job_id}", response_model=TTSJobResponse)
async def get_job_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return serialize_job(job)

@router.get("/tts/jobs/{job_id}/audio")
async def stream_audio_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job or job.status != "completed" or not job.audio_path:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_READY")
    return FileResponse(path=job.audio_path, media_type="audio/mpeg", filename=f"capvoice-{job.id}.mp3")
