import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.middleware.local_auth import LocalAuthMiddleware, validate_runtime_security
from app.services.audio_cleanup import cleanup_stale_temp_files
from app.services.audio_storage import close_http_client
from app.services.database_migrations import run_database_migrations
from app.services.job_recovery import recover_jobs
from app.services.logging_config import configure_logging
from app.services.raw_response_storage import cleanup_stale_raw_responses
from app.workers.queue_manager import queue_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    validate_runtime_security()
    await run_database_migrations()
    await asyncio.to_thread(
        cleanup_stale_temp_files,
        audio_dir=settings.audio_storage_dir,
        older_than_seconds=3_600,
    )
    await asyncio.to_thread(
        cleanup_stale_raw_responses,
        settings.raw_response_dir,
        older_than_seconds=settings.raw_provider_response_retention_seconds,
    )
    recovered_jobs = await recover_jobs()
    await queue_manager.start()
    for job_id, batch_pos in recovered_jobs:
        await queue_manager.enqueue(job_id, batch_position=batch_pos)
    try:
        yield
    finally:
        await queue_manager.stop()
        await close_http_client()


app = FastAPI(title="CapVoice Studio API", version="0.1.0", lifespan=lifespan)

app.add_middleware(LocalAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID", "X-Melody-Token"],
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import multiprocessing
    import sys

    import uvicorn

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)

    # Required for PyInstaller multi-processing support
    multiprocessing.freeze_support()
    logging.getLogger(__name__).info(
        "Uvicorn starting on http://%s:%s",
        settings.api_host,
        settings.api_port,
    )
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level="info",
    )
