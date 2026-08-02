from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.config import settings
from app.services.database_migrations import run_database_migrations
from app.services.job_recovery import recover_jobs

from app.workers.queue_manager import queue_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_database_migrations()
    recovered_ids = await recover_jobs()
    await queue_manager.start()
    for job_id in recovered_ids:
        await queue_manager.enqueue(job_id)
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

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    import sys
    
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)

    # Required for PyInstaller multi-processing support
    multiprocessing.freeze_support()
    print(f"Uvicorn starting on http://{settings.api_host}:{settings.api_port}", flush=True)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, reload=False, log_level="info")
