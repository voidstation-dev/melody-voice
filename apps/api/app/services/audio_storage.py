from pathlib import Path
import httpx

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/x-mpeg", "application/octet-stream", "video/mp4",
}

# Shared client with connection pooling for ultra-fast downloads
_http_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        _http_client = httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, max_redirects=5)
    return _http_client


def _has_audio_signature(path: Path) -> bool:
    with path.open("rb") as source:
        header = source.read(12)
    if header.startswith(b"ID3"):
        return True
    if len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0:
        return True
    return len(header) >= 8 and header[4:8] == b"ftyp"

async def download_audio(
    *,
    url: str,
    destination: Path,
    max_bytes: int = 50 * 1024 * 1024,
) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(".tmp")
    client = get_http_client()

    async with client.stream("GET", url) as response:
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unexpected content type: {content_type}")

        total = 0
        with temp_path.open("wb") as output:
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    if temp_path.exists():
                        temp_path.unlink()
                    raise ValueError("Audio file exceeds maximum size limit")
                output.write(chunk)

    if not _has_audio_signature(temp_path):
        temp_path.unlink(missing_ok=True)
        raise ValueError("Downloaded payload has no supported audio signature")

    temp_path.replace(destination)
    return content_type or "audio/mpeg", total
