from pathlib import Path
import httpx

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/x-mpeg", "application/octet-stream",
}

async def download_audio(
    *,
    url: str,
    destination: Path,
    max_bytes: int = 50 * 1024 * 1024,
) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(".tmp")
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=5) as client:
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

    temp_path.replace(destination)
    return content_type or "audio/mpeg", total
