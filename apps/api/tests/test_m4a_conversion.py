import asyncio
from pathlib import Path

import pytest

from app.utils.audio_utils import convert_mp3_to_m4a
from app.config import settings


class SuccessfulProcess:
    returncode = 0

    async def communicate(self):
        await asyncio.sleep(0.02)
        return b"", b""


@pytest.mark.asyncio
async def test_concurrent_m4a_requests_run_one_atomic_conversion(
    tmp_path: Path,
    monkeypatch,
):
    input_path = tmp_path / "job.mp3"
    output_path = tmp_path / "job.m4a"
    input_path.write_bytes(b"ID3audio")
    process_count = 0

    async def fake_subprocess(*command, **kwargs):
        nonlocal process_count
        process_count += 1
        Path(command[-1]).write_bytes(b"\x00\x00\x00\x18ftypM4A audio")
        return SuccessfulProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_subprocess)

    await asyncio.gather(
        *(convert_mp3_to_m4a(str(input_path), str(output_path)) for _ in range(5))
    )

    assert process_count == 1
    assert output_path.read_bytes().startswith(b"\x00\x00\x00\x18ftyp")
    assert not (tmp_path / "job.m4a.tmp").exists()
