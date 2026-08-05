import asyncio
import os
from pathlib import Path


async def combine_audio_parts(
    parts: list[Path],
    destination: Path,
) -> None:
    temporary = Path(f"{destination}.tmp")
    list_file = destination.with_name(f"{destination.stem}_list.txt")
    with list_file.open("w", encoding="utf-8") as output:
        for part in parts:
            output.write(f"file '{part.absolute()}'\n")

    ffmpeg_binary = os.environ.get("FFMPEG_BINARY_PATH", "ffmpeg")
    command = [
        ffmpeg_binary,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file.absolute()),
        "-c",
        "copy",
        "-f",
        "mp3",
        str(temporary.absolute()),
    ]

    print("Command:", command)
    print("List file content:")
    print(list_file.read_text())

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    print("FFmpeg stderr:", stderr.decode("utf-8"))
    if process.returncode != 0:
        print("Failed!")


async def main():
    p1 = Path(
        "/Users/phongvudzz/Library/Application Support/com.voidstation.voidmelody/audio/dummy_part0.mp3"
    )
    p2 = Path(
        "/Users/phongvudzz/Library/Application Support/com.voidstation.voidmelody/audio/dummy_part1.mp3"
    )

    # create valid mp3 files
    mp3_data = b"\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    p1.write_bytes(mp3_data)
    p2.write_bytes(mp3_data)

    dest = Path(
        "/Users/phongvudzz/Library/Application Support/com.voidstation.voidmelody/audio/dummy_final.mp3"
    )
    await combine_audio_parts([p1, p2], dest)

    p1.unlink()
    p2.unlink()


asyncio.run(main())
