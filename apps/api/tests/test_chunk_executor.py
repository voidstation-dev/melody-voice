import asyncio

import pytest

from app.services.chunk_executor import execute_chunks_bounded


@pytest.mark.asyncio
async def test_execute_chunks_bounded_never_exceeds_configured_concurrency():
    active = 0
    max_active = 0

    async def process_chunk(*, index: int, text: str):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return index, text.upper()

    results = [
        result
        async for result in execute_chunks_bounded(
            ["a", "b", "c", "d", "e"],
            concurrency=2,
            process_chunk=process_chunk,
        )
    ]

    assert max_active == 2
    assert sorted(results) == [
        (0, "A"),
        (1, "B"),
        (2, "C"),
        (3, "D"),
        (4, "E"),
    ]


@pytest.mark.asyncio
async def test_execute_chunks_bounded_cancels_remaining_work_after_failure():
    completed: list[int] = []

    async def process_chunk(*, index: int, text: str):
        if index == 1:
            raise RuntimeError("provider failed")
        await asyncio.sleep(0.05)
        completed.append(index)
        return index, text

    with pytest.raises(RuntimeError, match="provider failed"):
        async for _ in execute_chunks_bounded(
            ["a", "b", "c", "d"],
            concurrency=2,
            process_chunk=process_chunk,
        ):
            pass

    await asyncio.sleep(0)
    assert completed == []
