from pathlib import Path
import pytest
import respx
from httpx import Response
from app.services.audio_storage import download_audio

@pytest.mark.asyncio
@respx.mock
async def test_download_audio_success(tmp_path: Path):
    target_url = "https://cdn.example.com/audio.mp3"
    respx.get(target_url).mock(return_value=Response(200, content=b"ID3mockaudiodata", headers={"Content-Type": "audio/mpeg"}))

    dest = tmp_path / "test.mp3"
    mime, size = await download_audio(url=target_url, destination=dest)

    assert dest.exists()
    assert mime == "audio/mpeg"
    assert size == 16
