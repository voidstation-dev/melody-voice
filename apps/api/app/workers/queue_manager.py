import asyncio
import logging
from app.config import settings
from app.workers.tts_worker import execute_tts_job_step

logger = logging.getLogger(__name__)

class TTSQueueManager:
    def __init__(self, concurrency: int = 2):
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.concurrency = concurrency
        self.workers: list[asyncio.Task] = []

    async def start(self):
        logger.info("Starting TTS Queue Manager workers...")
        for i in range(self.concurrency):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)

    async def stop(self):
        logger.info("Stopping TTS Queue Manager workers...")
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []

    async def enqueue(self, job_id: str):
        await self.queue.put(job_id)
        logger.info(f"Enqueued job {job_id}. Queue size: {self.queue.qsize()}")

    async def _worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} started")
        while True:
            try:
                job_id = await self.queue.get()
                logger.info(f"Worker {worker_id} processing job {job_id}")
                try:
                    await execute_tts_job_step(job_id, worker_id=worker_id)
                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing job {job_id}: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered unexpected error: {e}")

queue_manager = TTSQueueManager(
    concurrency=settings.tts_queue_concurrency,
)
