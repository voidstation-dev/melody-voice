import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.models.custom_voice import CustomVoiceModel
from app.schemas.custom_voice import CustomVoiceListResponse, CustomVoiceResponse
from app.schemas.voice import VoiceListResponse, VoiceResponse
from app.services.voice_catalog import voice_catalog
from app.utils.audio_utils import get_audio_duration

router = APIRouter()


@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(
    language: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    raw_voices = voice_catalog.list_voices(language=language)

    if q:
        query_str = q.lower()
        raw_voices = [
            v
            for v in raw_voices
            if query_str in v.display_name.lower() or query_str in v.voice_type.lower()
        ]

    total = len(raw_voices)
    start = (page - 1) * page_size
    items = [
        VoiceResponse(
            id=v.voice_type,
            languageCode=v.language_code,
            languageShort=v.language_short,
            voiceType=v.voice_type,
            displayName=v.display_name,
            resourceId=v.resource_id,
            capturedAt=v.captured_at,
            providerId=v.provider_id,
        )
        for v in raw_voices[start : start + page_size]
    ]

    return VoiceListResponse(items=items, page=page, pageSize=page_size, total=total)


@router.post("/tts/voices/clone", response_model=CustomVoiceResponse, status_code=status.HTTP_201_CREATED)
async def clone_voice(
    audio_file: UploadFile = File(...),  # noqa: B008
    transcript: str = Form(...),
    display_name: str = Form(...),
    consent_given: bool = Form(...),
    session: AsyncSession = Depends(get_async_session)  # noqa: B008
):
    if not consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide consent to clone this voice."
        )

    # Validate audio type briefly
    if not audio_file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format. Please upload .wav, .mp3, .m4a, .flac, or .ogg."
        )

    settings.custom_voices_dir.mkdir(parents=True, exist_ok=True)
    temp_path = settings.custom_voices_dir / f"temp_{audio_file.filename}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Check duration
        duration = await get_audio_duration(temp_path)
        if duration is None or duration > 8.0:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio clip is too long ({duration}s). Maximum allowed is 8 seconds."
            )
        
        # Create model entry
        db_voice = CustomVoiceModel(
            display_name=display_name,
            transcript=transcript,
            consent_given=consent_given,
            reference_audio_path=""  # Will update after saving with ID
        )
        session.add(db_voice)
        await session.commit()
        await session.refresh(db_voice)

        # Rename file to ID
        final_path = settings.custom_voices_dir / f"{db_voice.id}{temp_path.suffix}"
        temp_path.rename(final_path)

        db_voice.reference_audio_path = str(final_path)
        await session.commit()
        await session.refresh(db_voice)

        return db_voice

    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process clone request: {exc}"
        )


@router.get("/tts/voices/custom", response_model=CustomVoiceListResponse)
async def list_custom_voices(
    session: AsyncSession = Depends(get_async_session),  # noqa: B008
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    stmt = select(CustomVoiceModel).order_by(CustomVoiceModel.created_at.desc())
    result = await session.execute(stmt)
    voices = result.scalars().all()
    
    total = len(voices)
    start = (page - 1) * page_size
    items = voices[start : start + page_size]

    return CustomVoiceListResponse(items=items, total=total)


@router.delete("/tts/voices/custom/{voice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_voice(
    voice_id: str,
    session: AsyncSession = Depends(get_async_session)  # noqa: B008
):
    stmt = select(CustomVoiceModel).where(CustomVoiceModel.id == voice_id)
    result = await session.execute(stmt)
    voice = result.scalars().first()

    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom voice not found."
        )

    # Delete audio file
    if voice.reference_audio_path:
        Path(voice.reference_audio_path).unlink(missing_ok=True)

    await session.delete(voice)
    await session.commit()
