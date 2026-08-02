import asyncio
import os
import tempfile
from pathlib import Path
import subprocess

async def convert_mp3_to_m4a(input_path: str, output_path: str) -> None:
    if os.path.exists(output_path):
        return

    ffmpeg_cmd = os.environ.get("FFMPEG_BINARY_PATH", "ffmpeg")
    # Run ffmpeg asynchronously
    cmd = [
        ffmpeg_cmd,
        "-y",
        "-i", input_path,
        "-c:a", "aac",
        "-b:a", "192k",
        "-vn",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg conversion failed: {stderr.decode('utf-8', errors='ignore')}")
