import json
from pathlib import Path

from app.services.provider_response_parser import extract_audio_urls


def test_extract_audio_urls_nested_json():
    fixture_path = (
        Path(__file__).parent / "fixtures" / "capcut_success_redacted.json"
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    urls = extract_audio_urls(payload)
    assert len(urls) == 1
    assert urls[0] == "https://cdn.example.invalid/audio/sample.mp3"


def test_extract_audio_urls_ranks_specific_audio_keys_before_generic_url():
    payload = {
        "url": "https://example.invalid/generic",
        "nested": {
            "download_url": "https://example.invalid/download.mp3",
            "audio_url": "https://example.invalid/audio.mp3",
            "speech_url": "https://example.invalid/speech.mp3",
        },
    }

    assert extract_audio_urls(payload) == [
        "https://example.invalid/speech.mp3",
        "https://example.invalid/audio.mp3",
        "https://example.invalid/download.mp3",
        "https://example.invalid/generic",
    ]
