from fastapi import APIRouter, Query

from app.schemas.voice import VoiceListResponse, VoiceResponse
from app.services.voice_catalog import voice_catalog

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
