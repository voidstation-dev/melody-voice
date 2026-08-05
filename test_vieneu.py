import asyncio
from app.database import AsyncSessionLocal
from app.services.tts_service import create_tts_job
from app.workers.queue_manager import queue_manager
import sys

async def main():
    async with AsyncSessionLocal() as session:
        job = await create_tts_job(
            session=session,
            text="Xin chào, đây là hệ thống thử nghiệm VieNeu.",
            voice_type="v3_tu_nhien_nam", # We'll need a real fixture voice ID
            voice_display_name="Nam (Tự Nhiên)",
            language_code="vi-VN",
            provider_id="vieneu",
        )
        print(f"Created job {job.id}")
        await queue_manager.enqueue(job.id)

if __name__ == "__main__":
    asyncio.run(main())
