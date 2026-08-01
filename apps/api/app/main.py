from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.config import settings
from app.database import init_database

from app.workers.queue_manager import queue_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    await queue_manager.start()
    yield
    await queue_manager.stop()

app = FastAPI(title="CapVoice Studio API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(api_router, prefix="/api/v1")
