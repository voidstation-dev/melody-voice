from fastapi import APIRouter

from app.api.v1 import (
    health,
    tts_batches,
    tts_jobs,
    voices,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(tts_jobs.router, tags=["TTS Jobs"])
api_router.include_router(tts_batches.router, tags=["TTS Batches"])
api_router.include_router(voices.router, tags=["Voices"])
