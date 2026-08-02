import asyncio
import logging
from collections.abc import Callable
from typing import Any

from app.config import settings
from app.providers.capcut_provider import CapCutProvider
from app.services.job_recovery import requeue_interrupted_job
from app.workers.tts_worker import execute_tts_job_step


logger = logging.getLogger(__name__)


def _default_provider_factory() -> CapCutProvider:
    return CapCutProvider(catalog_path=settings.capcut_catalog_path)


class TTSQueueManager:
    def __init__(
        self,
        concurrency: int = 2,
        *,
        provider_factory: Callable[[], Any] | None = None,
        shutdown_grace_seconds: float | None = None,
    ):
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.concurrency = concurrency
        self.provider_factory = provider_factory or _default_provider_factory
        self.shutdown_grace_seconds = (
            settings.tts_queue_shutdown_grace_seconds
            if shutdown_grace_seconds is None
            else shutdown_grace_seconds
        )
        self.workers: list[asyncio.Task] = []
        self.delayed_tasks: set[asyncio.Task] = set()
        self.enqueued_ids: set[str] = set()
        self._enqueue_lock = asyncio.Lock()
        self.accepting_jobs = False

    async def start(self) -> None:
        if self.workers:
            return
        self.accepting_jobs = True
        logger.info("Starting TTS queue workers")
        for worker_id in range(self.concurrency):
            self.workers.append(
                asyncio.create_task(
                    self._worker(worker_id),
                    name=f"tts-queue-{worker_id}",
                )
            )

    async def stop(self) -> None:
        self.accepting_jobs = False
        logger.info("Stopping TTS queue workers")

        for task in self.delayed_tasks:
            task.cancel()
        await asyncio.gather(*self.delayed_tasks, return_exceptions=True)
        self.delayed_tasks.clear()

        try:
            await asyncio.wait_for(
                self.queue.join(),
                timeout=self.shutdown_grace_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning("Queue shutdown grace period expired")

        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        while not self.queue.empty():
            try:
                job_id = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            async with self._enqueue_lock:
                self.enqueued_ids.discard(job_id)
            self.queue.task_done()

    async def enqueue(self, job_id: str) -> bool:
        async with self._enqueue_lock:
            if not self.accepting_jobs:
                raise RuntimeError("Queue manager is not accepting jobs")
            if job_id in self.enqueued_ids:
                return False
            self.enqueued_ids.add(job_id)

        try:
            await self.queue.put(job_id)
        except BaseException:
            async with self._enqueue_lock:
                self.enqueued_ids.discard(job_id)
            raise
        logger.info("Enqueued job %s; queue size=%s", job_id, self.queue.qsize())
        return True

    async def enqueue_after(
        self,
        job_id: str,
        *,
        delay_seconds: float,
    ) -> None:
        async def delayed_enqueue() -> None:
            await asyncio.sleep(delay_seconds)
            await self.enqueue(job_id)

        task = asyncio.create_task(
            delayed_enqueue(),
            name=f"tts-retry-{job_id}",
        )
        self.delayed_tasks.add(task)
        task.add_done_callback(self.delayed_tasks.discard)

    async def _worker(self, worker_id: int) -> None:
        provider = self.provider_factory()
        logger.info("TTS queue worker %s started", worker_id)
        while True:
            try:
                job_id = await self.queue.get()
            except asyncio.CancelledError:
                return

            try:
                await execute_tts_job_step(
                    job_id,
                    provider=provider,
                    worker_id=worker_id,
                )
            except asyncio.CancelledError:
                await asyncio.shield(requeue_interrupted_job(job_id))
                raise
            except Exception:
                logger.exception(
                    "Queue worker %s failed processing job %s",
                    worker_id,
                    job_id,
                )
            finally:
                async with self._enqueue_lock:
                    self.enqueued_ids.discard(job_id)
                self.queue.task_done()


queue_manager = TTSQueueManager(
    concurrency=settings.tts_queue_concurrency,
)
