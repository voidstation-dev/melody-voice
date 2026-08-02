import pytest

from app.services.chunk_executor import ChunkLimitExceeded, ensure_chunk_limit


def test_chunk_limit_rejects_job_without_truncating_chunks():
    chunks = [f"chunk-{index}" for index in range(121)]

    with pytest.raises(ChunkLimitExceeded) as exc_info:
        ensure_chunk_limit(chunks, max_chunks=120)

    assert exc_info.value.actual == 121
    assert exc_info.value.maximum == 120
    assert len(chunks) == 121
