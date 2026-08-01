from fastapi import APIRouter
from app.api.v1 import health, voices, tts_jobs

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(voices.router, tags=["Voices"])
api_router.include_router(tts_jobs.router, tags=["TTS Jobs"])
