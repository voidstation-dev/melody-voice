from fastapi import APIRouter
from app.services.voice_catalog import voice_catalog

router = APIRouter()

@router.get("/health")
async def health_check():
    voices = voice_catalog.list_voices()
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
