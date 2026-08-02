import json
import subprocess
from capcut_tts_api import CapCutClient
import sys
sys.path.append('.')
from app.services.provider_response_parser import extract_audio_urls
import os

def get_duration(url):
    ffmpeg_cmd = os.environ.get("FFMPEG_BINARY_PATH", "ffprobe")
    cmd = [ffmpeg_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", url]
    try:
        out = subprocess.check_output(cmd).decode().strip()
        return float(out)
    except:
        return 0.0

client = CapCutClient()
text = "Xin chào các bạn, đây là một đoạn text dài để kiểm tra tốc độ đọc của hệ thống."

print("Generating 1.0...")
r1 = client.generate_speech(text, rate="1.0")
urls1 = extract_audio_urls(r1)
if urls1:
    print("Duration 1.0:", get_duration(urls1[0]))

print("Generating 2.0...")
r2 = client.generate_speech(text, rate="2.0")
urls2 = extract_audio_urls(r2)
if urls2:
    print("Duration 2.0:", get_duration(urls2[0]))

# Try capcut sami rate syntax if they are integers? (e.g. rate="20" means 2.0x, rate="15" means 1.5x? Or rate="200")
print("Generating 20...")
r3 = client.generate_speech(text, rate="20")
urls3 = extract_audio_urls(r3)
if urls3:
    print("Duration 20:", get_duration(urls3[0]))

print("Generating 2...")
r4 = client.generate_speech(text, rate="2")
urls4 = extract_audio_urls(r4)
if urls4:
    print("Duration 2:", get_duration(urls4[0]))
