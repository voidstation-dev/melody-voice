import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_async_session
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.schemas.tts import CreateTTSJobRequest, TTSJobListResponse, TTSJobResponse, BatchJobCreateResponse
from app.services.tts_service import create_tts_job, get_job_by_id, list_jobs
from app.workers.tts_worker import execute_tts_job_step
from app.utils.text_utils import split_text_into_chunks, slugify_vietnamese

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
        batchId=job.batch_id,
        batchPosition=job.batch_position,
        sourceFileName=job.source_file_name,
        sourceFileSize=job.source_file_size,
        audioUrl=f"/api/v1/tts/jobs/{job.id}/audio" if job.status == "completed" else None,
        downloadUrl=f"/api/v1/tts/jobs/{job.id}/download" if job.status == "completed" else None,
        fileSize=job.audio_file_size,
        errorCode=job.error_code,
        errorMessage=job.error_message,
        createdAt=job.created_at.isoformat(),
        startedAt=job.started_at.isoformat() if job.started_at else None,
        updatedAt=job.updated_at.isoformat(),
        completedAt=job.completed_at.isoformat() if job.completed_at else None,
    )

from app.workers.queue_manager import queue_manager

@router.post("/tts/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=BatchJobCreateResponse)
async def create_job_endpoint(
    req: CreateTTSJobRequest,
    session: AsyncSession = Depends(get_async_session),
):
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    voices = provider.list_voices()
    matched = next((v for v in voices if v.voice_type == req.voiceType), None)
    
    if not matched:
        raise HTTPException(status_code=422, detail="VOICE_NOT_FOUND: Selected voice type does not exist in catalog")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided")

    batch_id = req.batchId if req.batchId else str(uuid.uuid4())
    batch_position = req.batchPosition if req.batchPosition is not None else 0
    
    job = await create_tts_job(
        session,
        text=req.text,
        voice_type=req.voiceType,
        voice_display_name=matched.display_name,
        language_code=matched.language_code,
        resource_id=matched.resource_id,
        rate=req.rate,
        batch_id=batch_id,
        batch_position=batch_position,
        source_file_name=req.sourceFileName,
        source_file_size=req.sourceFileSize,
    )
    
    await queue_manager.enqueue(job.id)

    return BatchJobCreateResponse(
        batchId=batch_id,
        jobs=[serialize_job(job)]
    )

@router.get("/tts/jobs", response_model=TTSJobListResponse)
async def list_jobs_endpoint(
    status: str | None = None,
    page: int = 1,
    pageSize: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    jobs, total = await list_jobs(session, status=status, page=page, page_size=pageSize)
    return TTSJobListResponse(
        items=[serialize_job(j) for j in jobs],
        page=page,
        pageSize=pageSize,
        total=total
    )

@router.get("/tts/jobs/{job_id}", response_model=TTSJobResponse)
async def get_job_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return serialize_job(job)

from app.utils.audio_utils import convert_mp3_to_m4a
import os

@router.get("/tts/jobs/{job_id}/audio")
async def stream_audio_endpoint(
    job_id: str, 
    format: str = "mp3",
    session: AsyncSession = Depends(get_async_session)
):
    job = await get_job_by_id(session, job_id)
    if not job or job.status != "completed" or not job.audio_path:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_READY")
    
    file_path = job.audio_path
    media_type = "audio/mpeg"
    
    if format == "m4a":
        m4a_path = job.audio_path.replace(".mp3", ".m4a")
        await convert_mp3_to_m4a(job.audio_path, m4a_path)
        file_path = m4a_path
        media_type = "audio/mp4"

    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=31536000, immutable",
    }

    return FileResponse(path=file_path, media_type=media_type, filename=f"capvoice-{job.id}.{format}", headers=headers)

@router.get("/tts/jobs/{job_id}/download")
async def download_audio_endpoint(
    job_id: str, 
    format: str = "mp3",
    session: AsyncSession = Depends(get_async_session)
):
    job = await get_job_by_id(session, job_id)
    if not job or job.status != "completed" or not job.audio_path:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_READY")
    
    file_path = job.audio_path
    media_type = "audio/mpeg"
    
    if format == "m4a":
        m4a_path = job.audio_path.replace(".mp3", ".m4a")
        await convert_mp3_to_m4a(job.audio_path, m4a_path)
        file_path = m4a_path
        media_type = "audio/mp4"

    slug = slugify_vietnamese(job.text)
    filename = f"{slug}.{format}"
        
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=31536000, immutable",
    }

    return FileResponse(
        path=file_path, 
        media_type=media_type, 
        filename=filename,
        headers=headers
    )

@router.delete("/tts/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    
    # Optional: Delete associated audio files
    if job.audio_path and os.path.exists(job.audio_path):
        try:
            os.remove(job.audio_path)
            # Delete m4a if exists
            m4a_path = job.audio_path.replace(".mp3", ".m4a")
            if os.path.exists(m4a_path):
                os.remove(m4a_path)
        except Exception as e:
            print(f"Error deleting audio files: {e}")

    await session.delete(job)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/tts/jobs/{job_id}/retry", response_model=TTSJobResponse)
async def retry_job_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    
    if job.status not in ["failed", "completed"]:
        raise HTTPException(status_code=400, detail="Only failed or completed jobs can be retried")
        
    # Reset job state
    job.status = "queued"
    job.progress = 0
    job.error_code = None
    job.error_message = None
    job.audio_path = None
    job.audio_file_size = None
    job.started_at = None
    job.completed_at = None
    
    await session.commit()
    await queue_manager.enqueue(job.id)
    
    return serialize_job(job)
