from app.services.provider_response_parser import extract_audio_urls

def test_extract_audio_urls_nested_json():
    payload = {
        "status": "success",
        "data": {
            "main_audio": '{"play_url": "https://v16-tts.capcut.com/audio/sample.mp3"}',
            "other": "https://example.com/not-audio"
        }
    }
    urls = extract_audio_urls(payload)
    assert len(urls) == 1
    assert urls[0] == "https://v16-tts.capcut.com/audio/sample.mp3"
