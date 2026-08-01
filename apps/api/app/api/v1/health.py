from fastapi import APIRouter
from app.config import settings
from app.providers.capcut_provider import CapCutProvider

router = APIRouter()

@router.get("/health")
async def health_check():
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    voices = provider.list_voices()
    return {
        "status": "ok",
        "service": "capvoice-api",
        "provider": {
            "name": "capcut-tts-api",
            "configured": True,
        },
        "catalog": {
            "voiceCount": len(voices),
            "latestCapturedAt": voices[0].captured_at if voices else None,
        },
    }
