from pathlib import Path

import httpx
import pytest
import respx
from httpx import Response

from app.exceptions import TTSJobError
from app.services import audio_storage
from app.services.audio_storage import (
    close_http_client,
    download_audio,
    validate_audio_file,
)


@pytest.mark.asyncio
@respx.mock
async def test_download_audio_success(tmp_path: Path):
    target_url = "https://cdn.example.com/audio.mp3"
    respx.get(target_url).mock(
        return_value=Response(
            200, content=b"ID3mockaudiodata", headers={"Content-Type": "audio/mpeg"}
        )
    )

    dest = tmp_path / "test.mp3"
    mime, size = await download_audio(url=target_url, destination=dest)

    assert dest.exists()
    assert mime == "audio/mpeg"
    assert size == 16


@pytest.mark.asyncio
@respx.mock
async def test_download_rejects_disallowed_content_type(tmp_path: Path):
    target_url = "https://cdn.example.com/not-audio"
    respx.get(target_url).mock(
        return_value=Response(
            200,
            content=b"<html>provider error</html>",
            headers={"Content-Type": "text/html"},
        )
    )
    destination = tmp_path / "invalid.mp3"

    with pytest.raises(ValueError, match="Unexpected content type"):
        await download_audio(url=target_url, destination=destination)

    assert not destination.exists()


@pytest.mark.asyncio
@respx.mock
async def test_download_accepts_octet_stream_payload_rejected_by_validation(
    tmp_path: Path,
):
    # Providers sometimes return application/octet-stream for audio. download_audio
    # streams it through (it does not inspect magic bytes); the audio-signature
    # rejection is the responsibility of validate_audio_file, invoked afterwards.
    target_url = "https://cdn.example.com/not-audio"
    respx.get(target_url).mock(
        return_value=Response(
            200,
            content=b"<html>provider error</html>",
            headers={"Content-Type": "application/octet-stream"},
        )
    )
    destination = tmp_path / "invalid.mp3"

    mime, _ = await download_audio(url=target_url, destination=destination)
    assert mime == "application/octet-stream"

    with pytest.raises(TTSJobError, match="invalid signature") as exc_info:
        validate_audio_file(destination, mime_type=mime)
    assert exc_info.value.code == "AUDIO_INVALID_CONTENT"
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
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
