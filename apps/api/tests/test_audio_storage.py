from pathlib import Path
import pytest
import respx
from httpx import Response
from app.services.audio_storage import download_audio
from app.services.audio_storage import close_http_client, validate_audio_file
from app.exceptions import TTSJobError
import app.services.audio_storage as audio_storage
import httpx

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


@pytest.mark.asyncio
@respx.mock
async def test_download_rejects_non_audio_payload(tmp_path: Path):
    target_url = "https://cdn.example.com/not-audio"
    respx.get(target_url).mock(
        return_value=Response(
            200,
            content=b"<html>provider error</html>",
            headers={"Content-Type": "application/octet-stream"},
        )
    )
    destination = tmp_path / "invalid.mp3"

    with pytest.raises(ValueError, match="audio signature"):
        await download_audio(url=target_url, destination=destination)

    assert not destination.exists()


@pytest.mark.asyncio
@respx.mock
async def test_download_rejects_mp4_provider_payload_for_mp3_pipeline(
    tmp_path: Path,
):
    target_url = "https://cdn.example.com/audio.mp4"
    respx.get(target_url).mock(
        return_value=Response(
            200,
            content=b"\x00\x00\x00\x18ftypM4A mock-audio",
            headers={"Content-Type": "audio/mp4"},
        )
    )
    destination = tmp_path / "provider-part.mp3"

    with pytest.raises(ValueError, match="content type"):
        await download_audio(url=target_url, destination=destination)

    assert not destination.exists()
    assert not destination.with_suffix(".tmp").exists()


class BrokenAudioStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b"ID3partial"
        raise httpx.ReadError("connection reset")


@pytest.mark.asyncio
async def test_download_removes_temp_file_when_stream_breaks(tmp_path: Path):
    async def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "audio/mpeg"},
            stream=BrokenAudioStream(),
        )

    audio_storage._http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )
    destination = tmp_path / "broken.mp3"
    try:
        with pytest.raises(httpx.ReadError):
            await download_audio(
                url="https://cdn.example.com/broken.mp3",
                destination=destination,
            )
        assert not destination.with_suffix(".tmp").exists()
        assert not destination.exists()
    finally:
        await close_http_client()


def test_final_audio_validation_rejects_invalid_signature(tmp_path: Path):
    output = tmp_path / "job.mp3"
    output.write_bytes(b"not audio")

    with pytest.raises(TTSJobError) as exc_info:
        validate_audio_file(output, mime_type="audio/mpeg")

    assert exc_info.value.code == "AUDIO_INVALID_CONTENT"
    assert exc_info.value.retryable is False
